# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
# Developed By: Mohammad Saleem Ali
#################################################################################
{
  "name"                 :  "MOB Group & Bundle Product Sync",
  "summary"              :  "Bundle and Group product bidirectional synchronization extension for MOB module",
  "category"             :  "sales",
  "version"              :  "1.0",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "website"              :  "https://store.webkul.com",
  "description"          :  "",
  "live_test_url"        :  "http://cscartodoo.webkul.com/",
  "depends"              :  ['odoo_magento_connect'],
  "data"                 :  [
                             'views/product_template_views.xml',
                            ],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  125,
  "currency"             :  "EUR",
  "pre_init_hook"        :  "pre_init_check",
}
