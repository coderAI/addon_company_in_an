odoo.define('mb_custom_api.ReportWidget', function (require) {
'use strict';

var core = require('web.core');
var Widget = require('web.Widget');
var Model = require('web.Model');
var Dialog = require('web.Dialog');

var QWeb = core.qweb;

var ReportWidget = Widget.extend({
    events: {
        'click .fa-pencil-square': 'clickPencil',
        'click .fa-pencil': 'clickPencil',
        'click .o_template_reports_foldable': 'fold',
        'click .o_template_reports_unfoldable': 'unfold',
        'click .too_many_title_folded': 'fold_tm',
        'click .too_many_title_unfoldable': 'unfold_tm',
        'click .fa-trash-o': 'rmContent',
        'click .o_template_reports_saved_summary > span': 'editSummary',
        'click .o_template_reports_edit_summary_pencil': 'editSummary',
        "click input[name='summary']": 'onClickSummary',
        "click button.saveSummary": 'saveSummary',
        'click button.saveContent': 'saveContent',
        'click .o_template_reports_add-footnote': 'footnoteFromDropdown',
        'click .o_template_reports_web_action': 'outboundLink',
        'click .o_template_reports_footnote_sup': 'goToFootNote',
    },
    init: function(parent, context, context_model, odoo_context, report_type) {
        this.context = context;
        this.context_model = context_model;
        this.odoo_context = odoo_context;
        this.report_type = report_type;
        this._super.apply(this, arguments);
    },
    start: function() {
        QWeb.add_template("/mb_custom_api/static/src/xml/template_report_line.xml");
        this.$('[data-toggle="tooltip"]').tooltip(); // start the tooltip widget
        var res = this._super.apply(this, arguments);
        core.bus.on("keydown", this, this.onKeyPress); // Bind key press to the right function
        return res;
    },
    update_context: function(update) {
        $.extend(this.context, update)
    },
    // Used to trigger actions
    outboundLink: function(e) {
        e.stopPropagation();
        var self = this;
        var id = $(e.target).parents('td').data('id');
        var action_id = $(e.target).data('action-id');
        var action_name = $(e.target).data('action-name');
        var active_id = $(e.target).data('active-id');
        var res_model = $(e.target).data('res-model');
        var view_id = $(e.target).data('view-id') || false;
        var action_domain = $(e.target).data('action-domain');
        var force_context = $(e.target).data('force-context');
        var additional_context = {};
        if (active_id || id) {
            additional_context = {active_id: active_id || id};
        }
        additional_context.from_report_id = self.odoo_context.id || null;
        additional_context.from_report_model = self.odoo_context.model;
        if (res_model && active_id) { // Open the view form of the given model
            return this.do_action({
                type: 'ir.actions.act_window',
                res_model: res_model,
                res_id: active_id,
                views: [[view_id, 'form']],
                target: 'current',
            });
        }
        if (res_model && action_domain) {
            return this.do_action({
                type: 'ir.actions.act_window',
                name: action_name ? action_name : '',
                res_model: res_model,
                domain: action_domain,
                views: [[false, 'list']],
            });
        }
        if (!_.isUndefined(force_context)) {
            var context = {
                date_filter: this.context.date_filter,
                date_filter_cmp: this.context.date_filter_cmp,
                date_from: this.report_type.date_range ? this.context.date_from : 'none',
                date_to: this.context.date_to,
                periods_number: this.context.periods_number,
                date_from_cmp: this.context.date_from_cmp,
                date_to_cmp: this.context.date_to_cmp,
            };
            additional_context.context = context;
            additional_context.force_context = true;
        }
        if (action_name && !action_id) { // If an action name is given, resolve it then do_action
            var dataModel = new Model('ir.model.data');
            var res = action_name.split('.');
            return dataModel.call('get_object_reference', [res[0], res[1]]).then(function (result) {
                additional_context.ctx_date_from = self.context.date_from + ' 00:00:00';
                additional_context.ctx_date_to = self.context.date_to + ' 23:59:59';
                additional_context.ctx_company_type = $(e.target).parents('td').data('customer-type');
                additional_context.ctx_list_company = $(e.target).parents('td').data('list-company');
//                additional_context.ctx_list_deparment = $(e.target).parents('td').data('list-deparment');
                additional_context.ctx_customer_state= $(e.target).parents('td').data('customer-state');
                console.log(additional_context);
                return self.do_action(result[1], {additional_context: additional_context});
            });
        }
        return this.do_action(action_id, {additional_context: additional_context});
    },
    onKeyPress: function(e) {
        if ((e.which === 70) && (e.ctrlKey || e.metaKey) && e.shiftKey) { // Fold all
            this.$(".o_template_reports_foldable").trigger('click');
        }
        else if ((e.which === 229) && (e.ctrlKey || e.metaKey) && e.shiftKey) { // Unfold all
            this.$(".o_template_reports_unfoldable").trigger('click');
        }
        else if ((e.which === 70) && (e.ctrlKey || e.metaKey) && e.shiftKey) { // Fold all
            this.$(".too_many").trigger('click');
        }
        else if ((e.which === 229) && (e.ctrlKey || e.metaKey) && e.shiftKey) { // Unfold too_many partner
            this.$(".too_many_unfold").trigger('click');
        }
    },
    // Changes the placeholder into an editable textarea and give it the focus
    onClickSummary: function(e) {
        e.stopPropagation();
        $(e.target).parents("div.o_template_reports_summary").html(QWeb.render("editSummary"));
        this.$("textarea[name='summary']").focus();
    },
    // When the user is done editing the summary
    saveSummary: function(e) {
        e.stopPropagation();
        e.preventDefault();
        var context_id = $(e.target).parents("div.o_template_reports_page").data("context");
        var summary = $(e.target).siblings("textarea[name='summary']").val().replace(/\r?\n/g, '<br />').replace(/\s+/g, ' ');
        if (summary) // If it isn't empty, display it normally
            $(e.target).parents("div.o_template_reports_summary").html(QWeb.render("savedSummary", {summary : summary}));
        else // If it's empty, delete the summary and display the default placeholder
            $(e.target).parents("div.o_template_reports_summary").html(QWeb.render("addSummary"));
        return this.context_model.call('edit_summary', [[parseInt(context_id, 10)], summary]);
    },
    // When clicking on the summary, display a textarea to edit it.
    editSummary: function(e) {
        e.stopPropagation();
        e.preventDefault();
        var $el = $(e.target).parents('.o_template_reports_summary').find('.o_template_reports_saved_summary span');
        var height = Math.max($el.height(), 100); // Compute the height that will be needed
        var text = $el.html().replace(/\s+/g, ' ').replace(/\r?\n/g, '').replace(/<br>/g, '\n').replace(/(\n\s*)+$/g, ''); // Remove unnecessary spaces and line returns
        var par = $el.parents("div.o_template_reports_summary");
        $el.parents("div.o_template_reports_summary").html(QWeb.render("editSummary", {summary: text})); // Render the textarea
        par.find("textarea").height(height); // Give it the right height
        this.$("textarea[name='summary']").focus(); // And the focus
    },
    clickPencil: function(e) {
        e.stopPropagation();
        e.preventDefault();
        if ($(e.target).parents("p.footnote").length > 0) { // If it's to edit a footnote at the bottom
            $(e.target).parents('.footnote').attr('class', 'o_template_reports_footnote_edit');
            var $el = $(e.target).parents('.o_template_reports_footnote_edit').find('span.text');
            var text = $el.html().replace(/\s+/g, ' ').replace(/\r?\n/g, '').replace(/<br>/g, '\n').replace(/(\n\s*)+$/g, ''); // Remove unnecessary spaces and line returns
            text = text.split('.'); // The text needs to be split into the number of the footnote and the actually content of the footnot
            var num = text[0];
            text = text[1];
            $el.html(QWeb.render("editContent", {num: num, text: text})); // Render the textarea to edit the footnote.
        }
    },
    fold: function(e) {
        if ($(e.target).hasClass('caret')) {
            return;
        }
        e.stopPropagation();
        e.preventDefault();
        var context_id = $(e.target).parents("div.o_template_reports_page").data("context");
        var el;
        var $el;
        var $nextEls = $(e.target).parents('tr').nextAll(); // Get all the next lines
        for (el in $nextEls) { // While domain lines are found, keep hiding them. Stop when they aren't domain lines anymore
            $el = $($nextEls[el]).find("td span.o_template_reports_domain_line_1, td span.o_template_reports_domain_line_2, td span.o_template_reports_domain_line_3");
            if ($el.length === 0)
                break;
            else {
                $($el[0]).parents("tr").hide();
            }
        }
        var active_id = $(e.target).parents('tr').find('td.o_template_reports_foldable').data('id');
        $(e.target).parents('tr').toggleClass('o_template_reports_unfolded'); // Change the class, rendering, and remove line from model
        $(e.target).parents('tr').find('td.o_template_reports_foldable').attr('class', 'o_template_reports_unfoldable ' + active_id);
        $(e.target).parents('tr').find('span.o_template_reports_foldable').replaceWith(QWeb.render("unfoldable", {lineId: active_id}));
        return this.context_model.call('remove_line', [[parseInt(context_id, 10)], parseInt(active_id, 10)]);
    },
    unfold: function(e) {
        if ($(e.target).hasClass('caret'))  {
            return;
        }
        e.stopPropagation();
        e.preventDefault();
        var self = this;
        var report_name = window.$("div.o_template_reports_page").data("report-name");
        var context_id = window.$("div.o_template_reports_page").data("context");
        var active_id = $(e.target).parents('tr').find('td.o_template_reports_unfoldable').data('id');
        return this.context_model.call('add_line', [[parseInt(context_id, 10)], parseInt(active_id, 10)]).then(function () { // First add the line to the model
            var el;
            var $el;
            var $nextEls = $(e.target).parents('tr').nextAll();
            var isLoaded = false;
            for (el in $nextEls) { // Look at all the element
                $el = $($nextEls[el]).find("td span.o_template_reports_domain_line_1, td span.o_template_reports_domain_line_2, td span.o_template_reports_domain_line_3");
                if ($el.length === 0) // If you find an element that is not a domain line, break out
                    break;
                else { // If you find an domain line element, it means the element has already been loaded and you only need to show it.
                    $($el[0]).parents("tr").show();
                    isLoaded = true;
                }
            }
            if (!isLoaded) { // If the lines have not yet been loaded
                var $cursor = $(e.target).parents('tr');
                new Model('vnnic.customer.report.context').call('get_full_report_name_by_report_name', [report_name]).then(function (result) {
                    var reportObj = new Model(result);
                    var f = function (lines) {// After loading the line
                        return self.context_model.call('get_footnotes_from_lines', [[parseInt(context_id, 10)], lines]).then(function (footnotes) {
                            var footnote;
                            for (footnote in footnotes) {
                                self.$("div.o_template_reports_page").append(QWeb.render("savedFootNote", {num: footnotes[footnote].number, note: footnotes[footnote].text}));
                            }
                            self.context_model.call('get_columns_types', [[parseInt(context_id, 10)]]).then(function (types) {
                                var line;
                                lines.shift();
                                for (line in lines) { // Render each line
                                    $cursor.after(QWeb.render("report_template_line", {l: lines[line], types: types}));
                                    $cursor = $cursor.next();
                                }
                            });
                        });
                    };
                    if (report_name === 'financial_report') { // Fetch the report_id first if needed
                        self.context_model.query(['report_id'])
                        .filter([['id', '=', context_id]]).first().then(function (context) {
                            reportObj.call('get_lines', [[parseInt(context.report_id[0], 10)], parseInt(context_id, 10), parseInt(active_id, 10)], {context : self.odoo_context}).then(f);
                        });
                    }
                    else {
                        reportObj.call('get_lines', [parseInt(context_id, 10), parseInt(active_id, 10)], {context : self.odoo_context}).then(f);
                    }
                });
            }
            $(e.target).parents('tr').toggleClass('o_template_reports_unfolded'); // Change the class, and rendering of the unfolded line
            $(e.target).parents('tr').find('td.o_template_reports_unfoldable').attr('class', 'o_template_reports_foldable ' + active_id);
            $(e.target).parents('tr').find('span.o_template_reports_unfoldable').replaceWith(QWeb.render("foldable", {lineId: active_id}));
        });
    },
    fold_tm: function(e) {

        if ($(e.target).hasClass('caret')) {
            return;
        }

        e.stopPropagation();
        e.preventDefault();

        var context_id = $(e.target).parents("div.o_template_reports_page").data("context");
        var el;
        var $el;
        var $nextEls = $(e.target).parents('tr').nextAll(); // Get all the next lines
        for (el in $nextEls) { // While domain lines are found, keep hiding them. Stop when they aren't domain lines anymore
            $el = $($nextEls[el]).find("td span.o_template_reports_domain_line_2, td span.o_template_reports_domain_line_3");
            if ($el.length === 0)
                break;
            else {
                $($el[0]).parents("tr").hide();
            }
        }



        var active_fi_id = $(e.target).parents('span').find('i.fa-caret-down').data('id');
        $(e.target).parents('span').find('i.fa-caret-down').attr('class', 'fa fa-fw fa-caret-right '); // Change the class, rendering, and remove line from model
        $(e.target).parents('span').find('i.fa-caret-down').replaceWith(QWeb.render("unfoldable", {lineId: active_fi_id}));
        $(e.target).parents('i').toggleClass('fa fa-fw fa-caret-right');



        var active_id = $(e.target).parents('tr').find('span.too_many_title_folded').data('id');
        $(e.target).parents('tr').toggleClass('too_many_title_unfolded'); // Change the class, rendering, and remove line from model
        $(e.target).parents('tr').find('span.too_many_title_folded').attr('class', 'too_many_title_unfoldable o_template_reports_caret_icon ' + active_id);
        $(e.target).parents('tr').find('span.too_many_title_folded').replaceWith(QWeb.render("unfoldable", {lineId: active_id}));
        return this.context_model.call('remove_line', [[parseInt(context_id, 10)], parseInt(active_id, 10)]);
    },
    unfold_tm: function(e) {

        if ($(e.target).hasClass('caret'))  {
            return;
        }

        e.stopPropagation();
        e.preventDefault();
        var self = this;
        var report_name = window.$("div.o_template_reports_page").data("report-name");
        var context_id = window.$("div.o_template_reports_page").data("context");
        var active_id = $(e.target).parents('tr').find('span.too_many_title_unfoldable').data('id');

        return this.context_model.call('add_line', [[parseInt(context_id, 10)], parseInt(active_id, 10)]).then(function () { // First add the line to the model
            var el;
            var $el;
            var $nextEls = $(e.target).parents('tr').nextAll();
            var isLoaded = false;
            for (el in $nextEls) { // Look at all the element
                $el = $($nextEls[el]).find("td span.o_template_reports_domain_line_2, td span.o_template_reports_domain_line_3");
                if ($el.length === 0) // If you find an element that is not a domain line, break out
                    break;
                else { // If you find an domain line element, it means the element has already been loaded and you only need to show it.
                    $($el[0]).parents("tr").show();
                    isLoaded = true;
                }
            }
            if (!isLoaded) { // If the lines have not yet been loaded
                var $cursor = $(e.target).parents('tr');
                new Model('vnnic.customer.report.context').call('get_full_report_name_by_report_name', [report_name]).then(function (result) {
                    var reportObj = new Model(result);
                    var f = function (lines) {// After loading the line
                        return self.context_model.call('get_footnotes_from_lines', [[parseInt(context_id, 10)], lines]).then(function (footnotes) {
                            var footnote;
                            for (footnote in footnotes) {
                                self.$("div.o_template_reports_page").append(QWeb.render("savedFootNote", {num: footnotes[footnote].number, note: footnotes[footnote].text}));
                            }
                            self.context_model.call('get_columns_types', [[parseInt(context_id, 10)]]).then(function (types) {
                                var line;
                                lines.shift();
                                for (line in lines) { // Render each line
                                    $cursor.after(QWeb.render("report_template_line", {l: lines[line], types: types}));
                                    $cursor = $cursor.next();
                                }
                            });
                        });
                    };
                    if (report_name === 'financial_report') { // Fetch the report_id first if needed
                        self.context_model.query(['report_id'])
                        .filter([['id', '=', context_id]]).first().then(function (context) {
                            reportObj.call('get_lines', [[parseInt(context.report_id[0], 10)], parseInt(context_id, 10), parseInt(active_id, 10)], {context : self.odoo_context}).then(f);
                        });
                    }
                    else {
                        reportObj.call('get_lines', [parseInt(context_id, 10), parseInt(active_id, 10)], {context : self.odoo_context}).then(f);
                    }
                });
            }








            var active_fi_id = $(e.target).parents('span').find('i.fa-caret-right').data('id');
            $(e.target).parents('span').find('i.fa-caret-right').attr('class', 'fa fa-fw fa-caret-down '); // Change the class, rendering, and remove line from model
            $(e.target).parents('span').find('i.fa-caret-right').replaceWith(QWeb.render("foldable", {lineId: active_fi_id}));
            $(e.target).parents('i').toggleClass('fa fa-fw fa-caret-down');




            $(e.target).parents('tr').toggleClass('too_many_title_unfoldable'); // Change the class, and rendering of the unfolded line
            //$(e.target).parents('').toggleClass('');
          //  $(e.target).parents('tr').toggleClass('too_many_title_unfoldable'); // Change the class, and rendering of the unfolded line
            $(e.target).parents('tr').find('span.too_many_title_unfoldable').attr('class', 'too_many_title_folded o_template_reports_caret_icon ' + active_id);
            $(e.target).parents('tr').find('span.too_many_title_unfoldable').replaceWith(QWeb.render("foldable", {lineId: active_id}));

        });
    },
    goToFootNote: function(e) {
        e.preventDefault();
        var elem = $(e.currentTarget).find('a').attr('href');
        this.trigger_up('scrollTo', {selector: elem});
    },
});

return ReportWidget;

});
