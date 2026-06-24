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
                form._listenerAdded = true; // Avoid adding multiple listeners if modal is opened multiple times
            }

            const categorySelect = modal.querySelector('select[name="expense_category"]');
            const receiptInput = modal.querySelector('input[name="receipt"]');
            const totalInput = modal.querySelector('input[name="total"]');
            const currencySelect = modal.querySelector('select[name="currency_id"]');

            if (!categorySelect || !receiptInput || !totalInput || !currencySelect) {
                return;
            }

            if (categorySelect && receiptInput) {
                const requireReceipt = receiptInput.dataset.requireAttachment === 'true';

                function updateReceiptRequired() {
                    const selectedOption = categorySelect.options[categorySelect.selectedIndex];
                    const selectedText = selectedOption ? selectedOption.text.trim() : '';

                    const isPerDiemMeals = selectedText === "Auditor: Per Diem - Meals";
                    const isAuditorMeal = selectedText === "Auditor Travel: Meal";

                    if (requireReceipt && isPerDiemMeals) {
                        receiptInput.required = false;
                        totalInput.value = 60;
                        totalInput.readOnly = true;
                        currencySelect.style.pointerEvents = 'none';
                        currencySelect.value = '2';
                    } else {
                        receiptInput.required = true;
                        totalInput.value = "";
                        totalInput.readOnly = false;
                        currencySelect.style.pointerEvents = '';
                        currencySelect.value = '';
                    }

                    // Override required if either exempt category is selected
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
                        field.value= "";
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

                    document.getElementById('name').value = this.dataset.name || '';
                    
                    payment_mode_field = document.getElementById('payment_mode');
                    if (payment_mode_field){
                        payment_mode_field.value = this.dataset.paymentMode || '';
                    }

                    document.getElementById('expense_date').value = this.dataset.expenseDate || '';
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