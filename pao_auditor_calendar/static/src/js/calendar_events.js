function ready() {

    const calendarEl = document.getElementById('calendar');
    const lang = document.getElementById("lang").value.slice(0, 2);
    const labels = {
        en: {
            today: 'Today',
            month: 'Month',
            week: 'Week',
            day: 'Day',
            list: 'List',
            allDayText: 'All day',
            noEventsMessage: 'No events to display',
            setDaysOffLabel: 'Set Days Off',
        },
        es: {
            today: 'Hoy',
            month: 'Mes',
            week: 'Semana',
            day: 'Día',
            list: 'Agenda',
            allDayText: 'Todo el día',
            noEventsMessage: 'No hay eventos para mostrar',
            setDaysOffLabel: 'Asignar días no laborales',
        }
    };

    $.ajax({
        type: 'POST',
        url: window.location.origin + '/auditor_agenda/get_events',
        dataType: 'json',
        beforeSend: function (xhr) { xhr.setRequestHeader('Content-Type', 'application/json'); },
        data: JSON.stringify({ jsonrpc: '2.0' }), //version of jsonrpc, important do not delete

        success: function (data) {
            if (data.error) {
                console.log(data)
                alert(data.error.data.debug)
                return
            }
            events = data.result
            initCalendar(events, lang)
        },

        error: function (jqXHR, status, err) {
            console.log(err)
            alert(err)
        },
    });


    function initCalendar(events, lang) {
        const calendar = new FullCalendar.Calendar(calendarEl, {
            header: {
                left: 'prev,next today setDaysOff', // Position these buttons on the left
                center: 'title', // The calendar title (e.g., "agosto de 2024") will be centered
                right: 'dayGridMonth,timeGridWeek,listMonth' // Add month, week, day, and list buttons to the right
            },
            customButtons: {
                setDaysOff: {
                    text: labels[lang].setDaysOffLabel,
                }
            },
            plugins: ['dayGrid', 'timeGrid', 'list', 'interaction'],
            firstDay: 1, // Monday as the first day of the week
            locale: lang,
            buttonText: {
                today: labels[lang].today, // Customize the text for the "Today" button
                month: labels[lang].month,
                week: labels[lang].week,
                day: labels[lang].day,
                list: labels[lang].list
            },
            views: {
                timeGridWeek: {
                    allDayText: labels[lang].allDayText
                },
                listMonth: {
                    noEventsMessage: labels[lang].noEventsMessage
                }
            },
            // defaultDate: initial_date,
            allDay: true,
            editable: false,
            selectable: false,
            unselectAuto: false,
            displayEventTime: false,
            events: events,
            eventClick: function (info) {
                info.jsEvent.preventDefault();

                let event = info.event
                let extra_info = info.event.extendedProps

                let startDate = new Date(event.start);
                let endDate = extra_info.display_end_date ? new Date(extra_info.display_end_date) : startDate;

                // Inject the details into the modal
                document.getElementById('event_name_value').innerHTML = event.title
                document.getElementById('event_start_value').innerHTML = formatDate(startDate)
                document.getElementById('event_end_value').innerHTML = formatDate(endDate)
                document.getElementById('raw_start_date').innerHTML = startDate.toISOString().split('T')[0];

                let rawEndDate = endDate
                rawEndDate.setDate(rawEndDate.getDate() - 1);
                document.getElementById('raw_end_date').innerHTML = rawEndDate.toISOString().split('T')[0];


                if (extra_info.type === 'days_off') {
                    document.getElementById('odoo_id').innerHTML = extra_info.odoo_id
                    document.getElementById('comments').innerHTML = extra_info.comments
                    document.getElementById('days_off_section').style.display = 'block';
                    document.getElementById('audits_section').style.display = 'none';
                    document.getElementById("download_ra_button").style.visibility = 'hidden';
                    document.getElementById("div_event_options").style.display = 'none';
                    if (extra_info.editable_event == 1){
                        document.getElementById("div_event_options").style.display = 'flex';
                    }
                } else {
                    generateAuditDetailsTable(extra_info);
                    document.getElementById('event_audit_location_value').innerHTML = extra_info.city + ', ' + extra_info.state
                    document.getElementById('event_audit_type_value').innerHTML = extra_info.type
                    document.getElementById('customer').innerHTML = extra_info.customer
                    document.getElementById('coordinator').innerHTML = extra_info.coordinator
                    document.getElementById('days_off_section').style.display = 'none';
                    document.getElementById('audits_section').style.display = 'block';
                    document.getElementById("div_event_options").style.display = 'none';

                    document.getElementById("download_ra_button").style.visibility = 'hidden';
                    if (extra_info.auditor_availability == 1) {
                        document.getElementById("download_ra_button").setAttribute('href', extra_info.ra_download_link);
                        document.getElementById("download_ra_button").style.visibility = 'visible';
                    }
                }

            },
            eventRender: function (info) {
                info.el.setAttribute('data-id', info.event.id);
                info.el.setAttribute('data-bs-toggle', 'modal');
                info.el.setAttribute('data-bs-target', '#eventModal');
            },
            datesRender: function (info) {
                filterEvents();
            }
        });

        document.getElementById("search_date").addEventListener('click', search_date)

        function search_date() {
            date = document.getElementById("start_date").value
            if (date != '') {
                calendar.gotoDate(date);
            }
        }

        function filterEvents() {
            const startOfMonth = calendar.view.activeStart;
            const endOfMonth = calendar.view.activeEnd;

            // Get all events
            const allEvents = calendar.getEvents();

            // Filter events based on the current month
            const visibleEvents = allEvents.filter(function (event) {
                return (event.start >= startOfMonth && event.start < endOfMonth) ||
                    (event.end && event.end > startOfMonth && event.end <= endOfMonth) ||
                    (event.start < startOfMonth && event.end > endOfMonth); // Overlapping events
            });

            visibleEvents.forEach(event => {
                event_type = event.extendedProps.type
                event_type_display = document.getElementById("check-" + event_type).checked
                const eventEls = document.querySelectorAll(`[data-id="${event.id}"]`);
                eventEls.forEach(eventEl => {
                    eventEl.style.display = event_type_display ? 'block' : 'none';
                });
            });
        }


        const eventsFilters = document.querySelectorAll('.check-toggle');

        // Add event listener to each checkbox
        eventsFilters.forEach((checkbox) => {
            checkbox.addEventListener('change', function () {
                filterEvents();
            });
        });

        calendar.render();

        const customButton = document.querySelector('.fc-setDaysOff-button'); // FullCalendar automatically adds class names
        if (customButton) {
            customButton.setAttribute('data-bs-toggle', 'modal');
            customButton.setAttribute('data-bs-target', '#addDaysModal');
        }

        document.querySelector('.fc-setDaysOff-button').addEventListener("click", function (event){
            document.getElementById('modalErrorAlert').style.display = 'none';
            document.getElementById("dayoff_id").value = ''
            document.getElementById("summary").value = ''
            document.getElementById("day_off_start_date").value = ''
            document.getElementById("end_date").value = ''
            document.getElementById("day_off_comments").value = ''
        })
    
        document.getElementById("edit_event_button").addEventListener("click", function (event){
            document.getElementById("close_event_details_button").click()
            document.querySelector('.fc-setDaysOff-button').click()
    
            document.getElementById("dayoff_id").value = document.getElementById("odoo_id").innerText
            document.getElementById("summary").value = document.getElementById("event_name_value").innerText
            document.getElementById("day_off_start_date").value = document.getElementById("raw_start_date").innerText
            document.getElementById("end_date").value = document.getElementById("raw_end_date").innerText
            document.getElementById("day_off_comments").value = document.getElementById("comments").innerText
        })
    }

    function formatDate(unformatted_date) {
        const options = {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
        };

        return new Intl.DateTimeFormat(lang, options).format(unformatted_date);
    }

    function generateAuditDetailsTable(info) {

        const tbody = document.getElementById('audit_details');
        tbody.innerHTML = '';

        info.order_lines.forEach(line => {
            const row = document.createElement('tr');

            // Create and append the cells to the row
            const description = document.createElement('td');
            description.textContent = line.description;
            row.appendChild(description);

            const organization = document.createElement('td');
            organization.textContent = line.organization;
            row.appendChild(organization);

            const registry_number = document.createElement('td');
            registry_number.classList.add("text-center");
            registry_number.textContent = line.registry_number;
            row.appendChild(registry_number);

            const start_date = document.createElement('td');
            start_date.textContent = formatDate(new Date(line.start_date + "T00:00:00"));
            row.appendChild(start_date);

            const end_date = document.createElement('td');
            end_date.textContent = formatDate(new Date(line.end_date + "T00:00:00"));
            row.appendChild(end_date);

            // Append the row to the tbody
            tbody.appendChild(row);
        });
    }

    function showAlert(message){
        document.getElementById("messageErrorAlert").innerText = message
        document.getElementById('modalErrorAlert').style.display = 'block';
    }

    document.getElementById("delete_event_button").addEventListener("click", function (event) {
        event.preventDefault();  // Prevent form from refreshing the page

        // Collect form data
        var formData = {
            dayoff_id: document.getElementById("odoo_id").innerText,
            jsonrpc: '2.0' //version of jsonrpc, important do not delete
        };

        // Make the AJAX request
        $.ajax({
            url: window.location.origin + '/auditor_agenda/delete_days_off',
            method: 'POST',
            contentType: "application/json",
            data: JSON.stringify(formData),
            success: function (data) {
                console.log(data)
                if (data.error || data.result.error){
                    error = data.error?.data?.debug || data.result.error
                    showAlert(error)
                    return
                }
                location.reload();
            },
            error: function (jqXHR, status, err) {
                console.log(err)
                alert(err)
            },
        });

    });


    document.getElementById("add_days_off_form").addEventListener("submit", function (event) {
        event.preventDefault();  // Prevent form from refreshing the page
        document.getElementById('modalErrorAlert').style.display = 'none';

        // Collect form data
        var formData = {
            dayoff_id: document.getElementById("dayoff_id").value,
            summary: document.getElementById("summary").value,
            start_date: document.getElementById("day_off_start_date").value,
            end_date: document.getElementById("end_date").value,
            comments: document.getElementById("day_off_comments").value,
            jsonrpc: '2.0' //version of jsonrpc, important do not delete
        };

        // Make the AJAX request
        $.ajax({
            url: window.location.origin + '/auditor_agenda/set_days_off',
            method: 'POST',
            contentType: "application/json",
            data: JSON.stringify(formData),
            success: function (data) {
                console.log(data)
                if (data.error || data.result.error){
                    error = data.error?.data?.debug || data.result.error
                    showAlert(error)
                    return
                }
                location.reload();
            },
            error: function (jqXHR, status, err) {
                console.log(err)
                alert(err)
            },
        });

    });

}

document.addEventListener('DOMContentLoaded', ready)