document.addEventListener("DOMContentLoaded", function () {
    let routeField = document.querySelector("#id_route");
    let stoppagesField = document.querySelector("#id_stoppages");

    function updateStoppages(routeId) {
        fetch(`/admin/get_stoppages/?route_id=${routeId}`)
            .then(response => response.json())
            .then(data => {
                stoppagesField.innerHTML = "";
                data.forEach(stoppage => {
                    let option = document.createElement("option");
                    option.value = stoppage.id;
                    option.textContent = stoppage.name;
                    stoppagesField.appendChild(option);
                });
            });
    }

    if (routeField) {
        routeField.addEventListener("change", function () {
            updateStoppages(this.value);
        });
    }
});
