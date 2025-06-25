async function getChildren(id) {
    const r = await fetch(`/api/categories/${id}`);
    return r.ok ? r.json() : [];
}

function noSubcatsHandler(level) {
    // «pass» — заглушка, когда подкатегорий нет
    console.log(`Уровень ${level}: подкатегорий нет`);
}

function clearBelow(level) {
    document.querySelectorAll("select[data-level]").forEach(el => {
        if (+el.dataset.level > level) el.remove();
    });
}

async function onChange(e) {
    const level = +e.target.dataset.level;
    const id = e.target.value;
    clearBelow(level);

    if (!id) return;

    const items = await getChildren(id);
    if (!items.length) {
        noSubcatsHandler(level);
        return;
    }

    const sel = document.createElement("select");
    sel.dataset.level = level + 1;
    sel.innerHTML = '<option value="">-- выберите --</option>' +
        items.map(i => `<option value="${i.id}">${i.name}</option>`).join("");
    sel.addEventListener("change", onChange);
    document.getElementById("subcats").appendChild(sel);
}

document.getElementById("level-1").addEventListener("change", onChange);