let links = Array.from(document.querySelectorAll("a"))

const example_link = "https://lers.google.com/api/u/2/download_file?listId=23657648&fileId=8190275&rapt=AEjHL4N026FDNNJPGE0YFYuh6vnpj5HBCwNZVkM1QJiK8DSSI5i4ex1uzQovDoH7MMiGsrUp3zBjso8-oDExBQsFvuFd_9bq5EjInVA6XOjriivox1N1gGE"

const re = /fileId=(\d+)/

function findFileNumber(text) {
    const [ticket, data, numberZip] = text.split("-")

    const fileNumber = Number(numberZip?.replace(".zip", "") || "")

    return fileNumber
}

let linksList = links.sort((a, b) => {
    return findFileNumber(a.text) - findFileNumber(b.text);
})
    .filter(a => a.href && a.href.includes("lers") && a.href.includes("api/u/2/download")).map((a, index) => {
        return `${index + 1}. ${a.text} - ` + a.href
    });

console.log(linksList.join("\n\n"));
