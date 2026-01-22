function FullScreen(imglink) {
    document.getElementById("FullImg").src = imglink;
    document.getElementById("FullScreenBlock").style.display = "block";
}

function CloseFullScreen() {
    document.getElementById("FullScreenBlock").style.display = "none";
}