(function () {
    const popoverTemplate = `<div class="popover" role="tooltip">
    <div class="popover-arrow"></div><h3 class="popover-header"></h3>
    <div class="share-link">
        <div class="popover-body"></div>
        <small>Click the link to copy to clipboard</small>
    </div>
</div>`;

    let popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        const popoverId = popoverTriggerEl.attributes['data-content-id'];
        if (popoverId) {
            const contentEl = $(`#${popoverId.value}`).html();
            const config = {
                container: 'body',
                content: contentEl,
                html: true,
                delay: {show: 300, hide: 1000},
            };
            return new bootstrap.Popover(popoverTriggerEl, config);
        } else {
            return new bootstrap.Popover(popoverTriggerEl, {template: popoverTemplate});
        }
    });
    const timeSpent = function () {
        let timeSpentScrolling = 0;

        let isHalted = false;
        let haltedStartTime, haltedEndTime;
        let totalHaltedTime = 0;

        const update_halt_state = () => {
            if (isHalted) {
                isHalted = false;
                haltedEndTime = new Date().getTime()
                totalHaltedTime += (haltedEndTime - haltedStartTime)
            } else {
                isHalted = true;
                haltedStartTime = new Date().getTime()
            }
        }

        // Listen for scroll events
        window.addEventListener('scroll', () => {
            timeSpentScrolling += 1.8;
            update_halt_state()
        });

        document.addEventListener("DOMContentLoaded", () => {
            const start = new Date().getTime();
            // AVERAGE SCROLLING INTERVAL - 39 seconds
            setInterval(() => {
                if (new Date().getTime() - start > 39000) {
                    update_halt_state();
                }
            }, 39000);

            window.addEventListener("beforeunload", () => {
                const end = new Date().getTime();
                update_halt_state()
                const totalTime = ((end - start)) - (timeSpentScrolling) - totalHaltedTime;
                console.log(totalTime + 'ms spent on page ' + window.location.href);
                // navigator.sendBeacon("https://topapi2.free.beeceptor.com", totalTime)
            });

        });
    }
    timeSpent();
})();