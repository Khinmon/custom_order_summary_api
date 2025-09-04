from odoo import http
from odoo.http import request
import json
from ._jwt import jwt_required

class OrderSummaryApi(http.Controller):

    @http.route('/api/v1/order-summary', type='json', auth='public', methods=['POST'], csrf=False)
    @jwt_required
    def order_summary(self, **kwargs):
        env = request.env
        data = request.get_json_data()
        delivery_ids = data.get("delivery_ids") or []
        template_keys = data.get("product_templates") or []
        limit = int(data.get("limit") or 100)
        offset = int(data.get("offset") or 0)

        tmpl_ids = set()
        if template_keys:
            ProductTmpl = env["product.template"].sudo()
            # partition keys
            numeric = [int(k) for k in template_keys if str(k).isdigit()]
            names = [k for k in template_keys if not str(k).isdigit() and "." not in str(k)]
            xids  = [k for k in template_keys if "." in str(k)]
            if numeric:
                tmpl_ids.update(ProductTmpl.search([('id','in',numeric)]).ids)
            if names:
                tmpl_ids.update(ProductTmpl.search([('name','in',names)]).ids)
            if xids:
                for xid in xids:
                    rec = env.ref(xid, raise_if_not_found=False)
                    if rec and rec._name == "product.template":
                        tmpl_ids.add(rec.id)

        # Delivery filter
        picking_ids = [int(x) for x in delivery_ids if str(x).isdigit()]
        print('**************picking_ids', picking_ids, tmpl_ids)

        sql = """
        WITH selected_moves AS (
            SELECT sm.*
            FROM stock_move sm
            LEFT JOIN stock_picking sp ON sm.picking_id = sp.id
            WHERE
                (%(filter_pickings)s IS FALSE OR sp.id = ANY(%(picking_ids)s))
        ),
        sol_base AS (
            SELECT sol.id AS sol_id,
                   sol.product_id,
                   pp.product_tmpl_id,
                   sol.product_uom_qty
            FROM sale_order_line sol
            JOIN product_product pp ON pp.id = sol.product_id
            WHERE
                (%(filter_templates)s IS FALSE OR pp.product_tmpl_id = ANY(%(tmpl_ids)s))
        ),
        delivered AS (
            SELECT sm.sale_line_id AS sol_id,
                   SUM(sm.product_uom_qty) AS delivered_qty
            FROM selected_moves sm
            JOIN stock_location l_dest ON l_dest.id = sm.location_dest_id
            WHERE sm.state = 'done'
              AND sm.sale_line_id IS NOT NULL
              AND l_dest.usage = 'customer'
            GROUP BY sm.sale_line_id
        ),
        manufactured AS (
            SELECT sm.product_id,
                   SUM(sm.product_uom_qty) AS manufactured_qty
            FROM selected_moves sm
            JOIN stock_location l_src ON l_src.id = sm.location_id
            JOIN stock_location l_dst ON l_dst.id = sm.location_dest_id
            WHERE sm.state = 'done'
              AND sm.production_id IS NOT NULL
              AND l_src.usage != 'customer' AND l_dst.usage = 'internal'
            GROUP BY sm.product_id
        ),
        sol_join AS (
            SELECT
                sb.product_tmpl_id,
                sb.product_id,
                sb.product_uom_qty AS ordered_qty,
                COALESCE(d.delivered_qty, 0) AS delivered_qty
            FROM sol_base sb
            LEFT JOIN delivered d ON d.sol_id = sb.sol_id
        ),
        tmpl_agg AS (
            SELECT
                pt.id AS template_id,
                pt.name AS template_name,
                COUNT(DISTINCT sj.product_id) AS variant_count,
                SUM(sj.ordered_qty) AS ordered_qty,
                SUM(sj.delivered_qty) AS delivered_qty,
                SUM(COALESCE(m.manufactured_qty, 0)) AS manufactured_qty
            FROM sol_join sj
            JOIN product_template pt ON pt.id = sj.product_tmpl_id
            LEFT JOIN manufactured m ON m.product_id = sj.product_id
            GROUP BY pt.id, pt.name
        )
        SELECT *
        FROM tmpl_agg
        ORDER BY template_name
        LIMIT %(limit)s OFFSET %(offset)s;
        """

        cr = env.cr
        cr.execute(sql, {
            "filter_pickings": bool(picking_ids),
            "picking_ids": picking_ids or None,
            "filter_templates": bool(tmpl_ids),
            "tmpl_ids": list(tmpl_ids) or None,
            "limit": limit,
            "offset": offset,
        })
        rows = cr.dictfetchall()

        # Total count (for pagination UI)
        count_sql = """
        SELECT COUNT(*) FROM (
            SELECT 1
            FROM sale_order_line sol
            JOIN product_product pp ON pp.id = sol.product_id
            WHERE (%(filter_templates)s IS FALSE OR pp.product_tmpl_id = ANY(%(tmpl_ids)s))
            GROUP BY pp.product_tmpl_id
        ) q;
        """
        cr.execute(count_sql, {
            "filter_templates": bool(tmpl_ids),
            "tmpl_ids": list(tmpl_ids) or None,
        })
        total = cr.fetchone()[0]

        return {
            "limit": limit,
            "offset": offset,
            "total_templates": total,
            "rows": rows,
        }
