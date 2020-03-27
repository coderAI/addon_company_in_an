odoo.define('working_order.reload_action', function (require) {
"use strict";
    var ActionManager = require('web.ActionManager');
    
     ActionManager.include({
        ir_actions_act_close_wizard_and_reload_view: function(action, options) {
            debugger;
            if (!this.dialog) {
                options.on_close();
            }
            this.dialog_stop();
            this.inner_widget.views[this.inner_widget.active_view.type].controller.reload();
            return $.when();
        },
    });
});