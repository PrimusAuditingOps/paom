function ready() {

    
    document.getElementById("pao_search_date").addEventListener('click', search_date);

    pao_date = document.getElementById("pao_start_date");
    pao_end_date = document.getElementById("pao_end_date");
    let params = new URLSearchParams(window.location.search);
    if (params.get('pao_date')){
        pao_date.value=params.get('pao_date');
    }
    else{
        pao_date.value = "";
    }
    if (params.get('pao_end_date')){
        pao_end_date.value=params.get('pao_end_date');
    }
    else{
        pao_end_date.value = "";
    }


    function search_date() {
        date = document.getElementById("pao_start_date").value;
        if (date != '') {

            let params = new URLSearchParams(window.location.search);
            params.set('pao_date', date);
            params.set('pao_end_date', date);
            window.location.href = window.location.pathname + '?' + params.toString();
        }
        else{
            let params = new URLSearchParams(window.location.search);
            params.delete('pao_date');
            params.delete('pao_end_date');
            window.location.href = window.location.pathname + '?' + params.toString();
        }
    }

}

document.addEventListener('DOMContentLoaded', ready)