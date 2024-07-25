// @match youtube.com

function killAd()
{
    for (const ad of document.getElementsByTagName("ytd-in-feed-ad-layout-renderer")) {
        ad.remove()
    }
}

setTimeout(function() {
    setInterval(killAd, 100);
}, 6000);