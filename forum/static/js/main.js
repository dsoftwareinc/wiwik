(function () {
    $(document).ready(function () {
        detectColorScheme();
        darkModeElement = document.getElementById('darkModeOn');
        if (darkModeElement && document.documentElement.getAttribute("data-theme") === "dark") {
            darkModeElement.textContent = "mode_night";
        }

        function detectColorScheme() {
            var theme = "light";    //default to light
            //local storage is used to override OS theme settings
            const val = localStorage.getItem("theme");
            if (val === "dark") {
                theme = "dark";
            } else if (val === 'light') {
                theme = "light";
            } else if (!window.matchMedia) {
                //matchMedia method not supported
                theme = "light";
            } else if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
                //OS theme setting detected as dark
                theme = "dark";
            }

            //dark theme preferred, set document with a `data-theme` attribute
            document.documentElement.setAttribute("data-theme", theme);
            localStorage.setItem('theme', theme);
        }

        if (darkModeElement) {
            $('#darkModeOn').click(function () {
                // document.querySelector('body').classList.add('bg-animation');
                var toDarkMode = this.textContent === "light_mode";
                if (toDarkMode) {
                    localStorage.setItem('theme', 'dark');
                    document.documentElement.setAttribute('data-theme', 'dark');
                    this.textContent = "mode_night";
                } else {
                    localStorage.setItem('theme', 'light');
                    document.documentElement.setAttribute('data-theme', 'light');
                    this.textContent = "light_mode";
                }
            })
        }

        $(document).on('click', '.share-link', function (el) {
            const message = el.target.textContent;
            if (typeof (navigator.clipboard) == 'undefined') {
                console.log('navigator.clipboard undefined - trying secondary approach to copy');
                var textArea = document.createElement("textarea");
                textArea.value = message;
                textArea.style.position = "fixed";  //avoid scrolling to bottom
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();

                try {
                    var successful = document.execCommand('copy');
                    var msg = successful ? 'successful' : 'unsuccessful';
                    console.log(msg);
                } catch (err) {
                    console.log('Was not possible to copy te text: ', err);
                }
                document.body.removeChild(textArea);
                return;
            }
            navigator.clipboard.writeText(message).then(function () {
                console.log(`Copied to clipboard: ${message}`);
            });
        });
    });
})();
