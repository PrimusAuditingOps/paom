function init() {
    console.log("Expense Portal JS Loaded");
    // my_expenses_details_view
    initPurchaseOrderSelector();
    initDisableSubmitButton();
    initExpenseModalListeners();
    initDeleteReport();

    // my_wallet_expenses_view
    initCheckAllExpenses();
    initAddExpensestoReport();
    initAddReceiptToExpense();
    initDeleteExpense();
    initEditExpense();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

function initPurchaseOrderSelector() {
    const purchaseField = document.getElementById('report_purchase_order');

    if (!purchaseField) {
        return;
    }

    purchaseField.addEventListener('change', function () {
        const redirectButton = document.getElementById('purchase_redirect');

        if (!redirectButton) {
            return;
        }

        redirectButton.href = '/my/purchase/' + this.value;
    });
}


function initDisableSubmitButton() {
    const form0 = document.getElementById('new_expense_form');
    const submitButton0 = document.getElementById('new_expense_button_form');

    if (!form0 || !submitButton0) {
        return;
    }

    form0.addEventListener('submit', function () {
        // Disable the submit button to prevent multiple submissions
        submitButton0.disabled = true;
    });
}


function initExpenseModalListeners() {
    document.querySelectorAll('.modal_expense_from_scratch').forEach(modal => {
        modal.addEventListener('shown.bs.modal', () => {
            const form = modal.querySelector('form');
            if (!form) return;

            const submitButton = modal.querySelector('button[type="submit"]');

            if (!form._listenerAdded) {
                form.addEventListener('submit', () => {
                    if (submitButton) {
                        submitButton.disabled = true;
                    }
                });
                form._listenerAdded = true;
            }

            const categorySelect = modal.querySelector('select[name="expense_category"]');
            const receiptInput = modal.querySelector('input[name="receipt"]');
            const totalInput = modal.querySelector('input[name="total"]');
            const currencySelect = modal.querySelector('select[name="currency_id"]');
            const internalNotes = modal.querySelector('input[name="description"]');
            const countryCode = modal.querySelector('input[name="country_code"]');
            const isExternalAuditor = modal.querySelector('input[name="is_external_auditor"]');

            const start_date = modal.querySelector('input[name="expense_date"]');
            const end_date = modal.querySelector('input[name="end_date"]');
            const endDateDiv = modal.querySelector('.end-date-div');

            let countryCode_value = countryCode ? countryCode.value : "";
            let isExternalAuditor_value = "";
            
            if (isExternalAuditor) {
                isExternalAuditor_value = isExternalAuditor.value;
            }

            if (!categorySelect || !receiptInput || !totalInput || !currencySelect) {
                return;
            }

            if (categorySelect && receiptInput) {
                const requireReceipt = receiptInput.dataset.requireAttachment === 'true';

                // Función para calcular días entre dos fechas
                function calculateDays() {
                    if (start_date && start_date.value && end_date && end_date.value) {
                        const startDateObj = new Date(start_date.value);
                        const endDateObj = new Date(end_date.value);
                        const timeDifference = endDateObj - startDateObj;
                        const daysDifference = Math.ceil(timeDifference / (1000 * 3600 * 24)) + 1; // +1 incluye el día inicial
                        return daysDifference > 0 ? daysDifference : 1;
                    }
                    return 1;
                }

                // Función para actualizar el total basado en días
                function updateTotalByDays() {
                    const days = calculateDays();
                    const dailyRate = 60;
                    totalInput.value = days * dailyRate;
                }

                function updateReceiptRequired() {
                    const selectedOption = categorySelect.options[categorySelect.selectedIndex];
                    const selectedText = selectedOption ? selectedOption.text.trim() : '';

                    const isPerDiemMeals = selectedText === "Auditor: Per Diem - Meals";
                    const isAuditorMeal = selectedText === "Auditor Travel: Meal";

                    if (requireReceipt && isPerDiemMeals) {
                        receiptInput.required = false;
                        if (internalNotes && isExternalAuditor_value.trim() == "True") {
                            internalNotes.required = false;
                        }

                        if (endDateDiv) {
                            endDateDiv.classList.remove('d-none');
                        }
                        
                        if (end_date) {
                            end_date.required = true;
                            
                            // Restringir end_date para que no sea menor que start_date
                            if (start_date && start_date.value) {
                                end_date.min = start_date.value;
                            }
                        }
                        
                        // Calcular total inicial
                        updateTotalByDays();
                        totalInput.readOnly = true;
                        
                        currencySelect.style.pointerEvents = 'none';
                        currencySelect.value = '2';

                        // Agregar evento listener para cambios en end_date
                        if (end_date && !end_date._perDiemListenerAdded) {
                            end_date.addEventListener('change', updateTotalByDays);
                            end_date._perDiemListenerAdded = true;
                        }
                        
                        if (start_date && !start_date._perDiemListenerAdded) {
                            start_date.addEventListener('change', () => {
                                // Actualizar el atributo min de end_date cuando start_date cambia
                                if (end_date) {
                                    end_date.min = start_date.value;
                                    // Si end_date es menor que start_date, igualarlo
                                    if (end_date.value && new Date(end_date.value) < new Date(start_date.value)) {
                                        end_date.value = start_date.value;
                                    }
                                }
                                updateTotalByDays();
                            });
                            start_date._perDiemListenerAdded = true;
                        }
                    } else {
                        receiptInput.required = true;
                        if (internalNotes && countryCode_value.trim() == "US") {
                            internalNotes.required = true;
                        }

                        // Deshacer cambios de Per Diem Meals
                        if (endDateDiv) {
                            endDateDiv.classList.add('d-none');
                        }
                        
                        if (end_date) {
                            end_date.required = false;
                            end_date.value = '';
                        }

                        totalInput.readOnly = false;
                        // totalInput.value = "";
                        currencySelect.style.pointerEvents = '';

                        // Remover event listeners de per diem
                        if (end_date && end_date._perDiemListenerAdded) {
                            end_date.removeEventListener('change', updateTotalByDays);
                            end_date._perDiemListenerAdded = false;
                        }
                        
                        if (start_date && start_date._perDiemListenerAdded) {
                            start_date.removeEventListener('change', updateTotalByDays);
                            start_date._perDiemListenerAdded = false;
                        }
                    }

                    // Override required si cualquiera de las categorías exentas está seleccionada
                    if (requireReceipt && (isPerDiemMeals || isAuditorMeal)) {
                        receiptInput.required = false;
                    }
                }

                updateReceiptRequired();
                categorySelect.addEventListener('change', updateReceiptRequired);
            }
        });
    });
}

function initCheckAllExpenses() {
    const selectAll = document.getElementById("select_all_expenses");
    if (!selectAll) return;

    selectAll.addEventListener("change", function () {
        const checkboxes = document.querySelectorAll(".expense-checkbox");
        checkboxes.forEach(cb => {
            if (!cb.disabled) {
                cb.checked = selectAll.checked;
            }
        });
    });
}

function initAddExpensestoReport() {

    addExpensesToReportForm = document.getElementById('add_expenses_to_report_form')

    if (!addExpensesToReportForm) return;

    addExpensesToReportForm.addEventListener('submit', function () {
        event.preventDefault();

        var form = this;
        var checkboxes = document.querySelectorAll('input[name="selected_expenses"]:checked');

        // Iterate through the selected checkboxes
        checkboxes.forEach(function (checkbox) {
            // Create a hidden input element for each selected checkbox
            var hiddenInput = document.createElement('input');
            hiddenInput.type = 'hidden';
            hiddenInput.name = 'selected_expenses';
            hiddenInput.value = checkbox.value;

            // Append the hidden input to the form
            form.appendChild(hiddenInput);
        });

        // Submit the form
        form.submit();
    });
}


function initAddReceiptToExpense() {
    document.querySelectorAll('.add-receipt-btn').forEach(button => {
        button.addEventListener('click', function () {
            document.getElementById('add_receipt_expense_id').value =
                this.dataset.expenseId;

            const editNote = document.getElementById('edit_note');
            if (editNote) {
                editNote.classList.add('d-none');
            }

            document.getElementById('expense_category').value = "";
            document.getElementById('description').value = "";

            document.querySelectorAll('.edit_full_info').forEach(container => {
                container.classList.add('d-none');

                container
                    .querySelectorAll('input, select, textarea')
                    .forEach(field => {
                        field.required = false;
                        field.value = "";
                    });
            });
        });
    });
}

function initDeleteExpense() {
    document.querySelectorAll('.delete-expense-btn').forEach(button => {
        button.addEventListener('click', function () {
            document.getElementById('delete_expense_id').value =
                this.dataset.expenseId;
        });
    });
}

function initDeleteReport() {
    document.querySelectorAll('.delete-report-btn').forEach(button => {
        button.addEventListener('click', function () {
            document.getElementById('delete_report_id').value =
                this.dataset.reportId;
        });
    });
}

function initEditExpense() {
    document.querySelectorAll('.edit-expense-btn').forEach(button => {
        button.addEventListener('click', function () {

            document.getElementById('add_receipt_expense_id').value =
                this.dataset.expenseId;

            const editNote = document.getElementById('edit_note');
            if (editNote) {
                editNote.classList.remove('d-none');
            }

            document.getElementById('expense_category').value =
                this.dataset.categoryId || '';

            document.getElementById('description').value =
                this.dataset.description || '';

            document.querySelectorAll('input[name="tax_ids"]').forEach(cb => {
                cb.checked = false;
            });

            const taxIds = (this.dataset.taxIds || '')
                .split(',')
                .filter(Boolean);

            document.querySelectorAll('input[name="tax_ids"]').forEach(cb => {
                cb.checked = taxIds.includes(cb.value);
            });

            const uploadedByStatement =
                String(this.dataset.uploadedByStatement).toLowerCase() === 'true';

            document.querySelectorAll('.edit_full_info').forEach(container => {
                if (!uploadedByStatement) {

                    container.classList.remove('d-none');

                    container
                        .querySelectorAll('input, select, textarea')
                        .forEach(field => {
                            field.required = true;
                        });

                    name_field = document.getElementById('name');
                    if (name_field) {
                        name_field.value = this.dataset.name || '';
                    }

                    payment_mode_field = document.getElementById('payment_mode');
                    if (payment_mode_field) {
                        payment_mode_field.value = this.dataset.paymentMode || '';
                    }

                    document.getElementById('expense_date').value = this.dataset.expenseDate || '';
                    document.getElementById('end_date').value = this.dataset.endDate || '';
                    document.getElementById('total').value = this.dataset.total || ''
                    document.getElementById('currency_id').value = this.dataset.currencyId || ''
                } else {

                    container.classList.add('d-none');

                    container
                        .querySelectorAll('input, select, textarea')
                        .forEach(field => {
                            field.required = false;
                        });
                }
            });
        });
    });
}