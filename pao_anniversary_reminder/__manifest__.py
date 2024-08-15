{
    "name": "PAO: Anniversary Reminder",
    "version": "1.0",
    "author": "Manuel Uzueta Gil",
    "category": "",
    "website": "https://paomx.com",
    "depends": ["base", "purchase", "servicereferralagreement"],
    'data': [
        'security/ir.model.access.csv',
        
        'data/cron_data.xml',
        'data/mail_template.xml',
        
        'views/reminder_portal_templates.xml',
        'views/send_reminder_view_form.xml',
        'views/pao_anniversary_reminder_views.xml',
        'views/mail_templates_manager.xml',
        'views/menu_application_anniversary_reminder.xml',
    ],
    'license': 'LGPL-3',
}