from odoo import api, fields, models


class ExternalSO(models.AbstractModel):
    _name = 'external.so'
    _inherit = 'external.so'

    @api.model
    def check_contract_of_service(self, num_date=0):
        query = """
        select A.* from (
            SELECT p.ref, p.name AS customer_name, p.email AS customer_email, sc.name AS contract_ref, pt.name,
            pc.name AS category_name, sol.date_active::DATE, sol.date_active::DATE + 10 AS last_date, sol.register_type,
            e.name_related, e.work_email, e.mobile_phone, so.company_id, p.company_type
            FROM sale_order_line sol
                LEFT JOIN product_product pp ON (pp.id = sol.product_id)
                LEFT JOIN product_template pt ON (pt.id = pp.product_tmpl_id)
                LEFT JOIN product_category pc ON (pc.id = sol.product_category_id)
                LEFT JOIN sale_order so ON (so.id = sol.order_id)
                LEFT JOIN mb_sale_contract sc ON (sc.id = so.contract_id)
                LEFT JOIN res_partner p ON (p.id = so.partner_id)
                LEFT JOIN resource_resource r ON (so.user_id = r.user_id)
                LEFT JOIN hr_employee e ON (e.resource_id = r.id)
            WHERE so.fully_paid IS TRUE
            AND sol.date_active::DATE + %s = NOW()::DATE
            AND (sc.state NOT IN ('submit', 'return', 'refuse_op', 'cancel') OR so.contract_id IS NULL)
            AND pc.require_contract IS TRUE
            AND sol.service_status = 'done'
            AND sol.register_type = 'register'
            UNION ALL
            SELECT p.ref, p.name AS customer_name, p.email AS customer_email, sc.name AS contract_ref, pt.name,
            pc.name AS category_name, sol.date_active::DATE, sol.date_active::DATE + 10 AS last_date, sol.register_type,
            e.name_related, e.work_email, e.mobile_phone, so.company_id, p.company_type
            FROM sale_order_line sol
                LEFT JOIN product_product pp ON (pp.id = sol.product_id)
                LEFT JOIN product_template pt ON (pt.id = pp.product_tmpl_id)
                LEFT JOIN product_category pc ON (pc.id = sol.product_category_id)
                LEFT JOIN sale_order so ON (so.id = sol.order_id)
                LEFT JOIN mb_sale_contract sc ON (sc.id = so.contract_id)
                LEFT JOIN res_partner p ON (p.id = so.partner_id)
                LEFT JOIN resource_resource r ON (so.user_id = r.user_id)
                LEFT JOIN hr_employee e ON (e.resource_id = r.id)
            WHERE so.fully_paid IS TRUE
            AND sol.date_active::DATE + %s = NOW()::DATE
            AND sc.state IN ('signed', 'sent_cus', 'received', 'refuse_cont')
        )
        A GROUP BY 
            A.ref, A.customer_name, A.customer_email, A.contract_ref, A.name, A.category_name, A.date_active,
            A.last_date, A.register_type, A.name_related, A.work_email, A.mobile_phone, A.company_id, A.company_type
        ORDER BY A.customer_name, A.contract_ref
        """ % (num_date, num_date)
        self.env.cr.execute(query)
        data = {}
        results = self.env.cr.fetchall()
        for result in results:
            if len(result) != 14:
                return 'Can not get data!'
            try:
                if ((result[3] or '') + result[0]) not in data:
                    data[(result[3] or '') + result[0]] = {
                        '"customer_ref"': '\"' + (result[0] or '') + '\"',
                        '"customer_name"': '\"' + (result[1] or '') + '\"',
                        '"customer_email"': '\"' + (result[2] or '') + '\"',
                        '"contract_ref"': '\"' + (result[3] or '') + '\"',
                        '"services"': [{
                            '"service_name"': '\"' + (result[4] or '') + '\"',
                            '"category_name"': '\"' + (result[5] or '') + '\"',
                            '"date_active"': '\"' + (result[6] or '') + '\"',
                            '"date_finish"': '\"' + (result[7] or '') + '\"',
                            '"register_type"': '\"' + (result[8] or '') + '\"'
                        }],
                        '"employee_name"': '\"' + (result[9] or '') + '\"',
                        '"employee_email"': '\"' + (result[10] or '') + '\"',
                        '"employee_phone"': '\"' + (result[11] or '') + '\"',
                        '"company_id"': result[12],
                        '"company_type"': '\"' + (result[13] or '') + '\"',
                    }
                else:
                    data[(result[3] or '') + result[0]]['"services"'].append({
                        '"service_name"': '\"' + (result[4] or '') + '\"',
                        '"category_name"': '\"' + (result[5] or '') + '\"',
                        '"date_active"': '\"' + (result[6] or '') + '\"',
                        '"date_finish"': '\"' + (result[7] or '') + '\"',
                        '"register_type"': '\"' + (result[8] or '') + '\"'
                    })
            except UnicodeDecodeError:
                return '[BUG] {}'.format(result)

        return data.values()
