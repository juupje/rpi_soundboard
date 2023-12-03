function play(page, track) {
    let xhr = new XMLHttpRequest();
    xhr.open("POST", "/play/"+page+"/"+track, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function() {
        if(xhr.readyState == 4) {
            if(xhr.status != 200) {
                alert("Oeps, foutje: " + xhr.status);
            }
            let response = JSON.parse(xhr.responseText);
            if(response["success"] == true) {
                let box = document.getElementById("popup");
                let content = box.children[0];
                content.innerHTML = "success!";
                box.classList.remove("hide-popup");
                setTimeout(() => {
                    box.classList.add("hide-popup");
                }, 1000);
            } else
                alert("Er ging iets mis...\n" + response["message"]);
        }
    }
    console.log(JSON.stringify({page, track}));
    xhr.send(JSON.stringify({page, track}));
}