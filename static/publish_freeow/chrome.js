CHROME_ID_2 = localStorage.removeItem('CHROME_ID_2')
window.addEventListener("ChromeID", function (event) {

    CHROME_ID_2 = event.detail.id;
    localStorage.setItem('CHROME_ID_2', CHROME_ID_2)
}, false);




