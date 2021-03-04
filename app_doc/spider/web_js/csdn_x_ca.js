f = function () {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (function (e) {
            var n = 16 * Math.random() | 0
                , t = "x" === e ? n : 3 & n | 8;
            return t.toString(16)
        }
    ))
};
