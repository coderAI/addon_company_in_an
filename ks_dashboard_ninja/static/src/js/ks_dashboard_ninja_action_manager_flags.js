odoo.define('ks_dashboard_ninja.ActionManager', function (require) {
"use strict";

/**
 * The purpose of this file is to patch the ActionManager to properly generate
 * the flags for the 'ir.actions.act_window' of model 'ks_dashboard_ninja.board'.
 */

var ActionManager = require('web.ActionManager');

ActionManager.include({

    ir_actions_act_window: function (action, options) {
        if (action.res_model === 'ks_dashboard_ninja.board' &&
                                    action.xml_id !== "ks_dashboard_ninja.board_form_tree_action_window") {
            action.target = 'inline';
            _.extend(action.flags, {
                headless: true,
                views_switcher: false,
                display_title: false,
                search_view: false,
                pager: false,
                sidebar: false,
                action_buttons: false
            });
        }
        return this._super(action, options);
    },

});

});
