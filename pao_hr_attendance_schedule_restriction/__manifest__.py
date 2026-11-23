{
    "name": "PAO Attendance Schedule Restriction",
    "summary": "Restrict check-in/check-out to the employee working schedule with configurable tolerances",
    "version": "17.0.1.0.0",
    'author':'Samuel Castro',
    "website": "https://paomx.com",
    "category": "Human Resources/Attendances",
    "depends": ["hr_attendance", "resource"],
    "data": [
        "views/resource_calendar_views.xml",
        "views/hr_attendance_views.xml",
    ],
    "installable": True,
    "license": "LGPL-3",
}
