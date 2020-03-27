from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import html_escape
import json


class HrEmployeeReportController(http.Controller):

    @http.route('/mb_custom_api/<string:output_format>/<string:report_name>/<string:report_id>', type='http', auth='user')
    def report(self, output_format, report_name, token, report_id=None, **kw):
        uid = request.session.uid
        context_obj = request.env['vnnic.customer.report.context']
        context= context_obj.sudo().browse(int(report_id))

        try:
            if output_format == 'xlsx':
                response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.ms-excel'),
                        ('Content-Disposition', 'attachment; filename=VNNIC_report.xlsx;')
                    ]
                )
                context.get_xlsx(response)
                response.set_cookie('fileToken', token)
                return response
            if output_format == 'pdf':
                response = request.make_response(
                    context.get_pdf(),
                    headers=[
                        ('Content-Type', 'application/pdf'),
                        ('Content-Disposition', 'attachment; filename=VNNIC_report.pdf;')
                    ]
                )
                response.set_cookie('fileToken', token)
                return response
        except Exception, e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))
        else:
            return request.not_found()
