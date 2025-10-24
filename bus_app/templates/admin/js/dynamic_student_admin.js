document.addEventListener("DOMContentLoaded", function () {
    var schoolDropdown = document.getElementById("id_school");
    var programDropdown = document.getElementById("id_program");

    var routeDropdown = document.getElementById("id_route");
    var stoppageDropdown = document.getElementById("id_stoppage");

    // ✅ **Fetch Programs when School is Selected**
    schoolDropdown.addEventListener("change", function () {
        var schoolId = this.value;
        programDropdown.innerHTML = '<option value="">Loading...</option>';

        fetch(`/get-programs/?school_id=${schoolId}`)
            .then(response => response.json())
            .then(data => {
                programDropdown.innerHTML = '<option value="">Select Program</option>';
                data.forEach(program => {
                    programDropdown.innerHTML += `<option value="${program.id}">${program.name}</option>`;
                });
            });
    });

    // ✅ **Fetch Stoppages when Route is Selected**
    routeDropdown.addEventListener("change", function () {
        var routeId = this.value;
        stoppageDropdown.innerHTML = '<option value="">Loading...</option>';

        fetch(`/get-stoppages/?route_id=${routeId}`)
            .then(response => response.json())
            .then(data => {
                stoppageDropdown.innerHTML = '<option value="">Select Stoppage</option>';
                data.forEach(stoppage => {
                    stoppageDropdown.innerHTML += `<option value="${stoppage.id}">${stoppage.name}</option>`;
                });
            });
    });
});
