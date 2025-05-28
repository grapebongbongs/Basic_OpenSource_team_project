document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.div1').forEach(function (div) {
        div.addEventListener('click', function () {
            const monaCd = this.getAttribute('data-mona-cd');
            console.log("클릭됨! mona_cd =", monaCd); // ✅ 이 로그가 뜨는지 확인

            if (monaCd) {
                window.location.href = `/vote/${monaCd}/`;
            }
        });
    });
});