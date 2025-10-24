document.addEventListener("DOMContentLoaded", function() {
    let routeField = document.getElementById("id_route");  // Route Dropdown
    let stoppagesField = document.getElementById("id_stoppages");  // MultiSelect Box

    if (!routeField || !stoppagesField) return;  // Ensure elements exist

    routeField.addEventListener("change", function() {
        let routeId = routeField.value;
        if (routeId) {
            fetch(`/get-stoppages/?route_id=${routeId}`)
                .then(response => response.json())
                .then(data => {
                    // ✅ MultiSelect Box Ka Data Clear Karna
                    stoppagesField.innerHTML = "";  
                    
                    // ✅ Naye Stoppages Add Karna
                    data.forEach(stoppage => {
                        let option = new Option(stoppage.name, stoppage.id);
                        stoppagesField.add(option);
                    });
                })
                .catch(error => console.error("Error fetching stoppages:", error));
        }
    });
});
