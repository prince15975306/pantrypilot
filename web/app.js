
const $ = (selector) => document.querySelector(selector);

const state = {
    tools: [],
    meals: [],
    shoppingRecipeIds: [],
    pantry: [],
    preferences: {}
};

function showMessage(message, isError = false) {
    const box = $("#message");
    box.textContent = message;
    box.classList.toggle("error", isError);
}

async function mcpRequest(method, params = {}) {
    const response = await fetch("/mcp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            jsonrpc: "2.0",
            id: Date.now(),
            method,
            params
        })
    });

    if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
    }

    const data = await response.json();

    if (data.error) {
        throw new Error(data.error.message || "MCP request failed");
    }

    return data.result;
}


async function callTool(name, args = {}) {
    const result = await mcpRequest("tools/call", {
        name,
        arguments: args
    });

    if (result?.isError) {
        const message = (result.content || [])
            .map(item => item.text || "")
            .filter(Boolean)
            .join("\n");

        throw new Error(message || `${name} failed`);
    }

    // Prefer structured data returned by the backend.
    if (result?.structuredContent) {
        return result.structuredContent;
    }

    // Fall back to parsing text if structured data is unavailable.
    const textContent = (result?.content || [])
        .filter(item => item.type === "text")
        .map(item => item.text)
        .join("\n");

    if (!textContent) return result;

    try {
        return JSON.parse(textContent);
    } catch {
        return textContent;
    }
}


function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[char]);
}

function formatQuantity(item) {
    return `${item.quantity ?? ""} ${item.unit ?? ""}`.trim();
}

function renderEmpty(container, message) {
    container.innerHTML = "";
    const p = document.createElement("p");
    p.className = "empty-state";
    p.textContent = message;
    container.appendChild(p);
}

function getArray(data, ...keys) {
    if (Array.isArray(data)) return data;

    for (const key of keys) {
        if (Array.isArray(data?.[key])) return data[key];
    }

    return [];
}

function renderPantry(items) {
    state.pantry = items;
    $("#pantry-count").textContent = items.length;

    const list = $("#pantry-list");
    list.innerHTML = "";

    if (!items.length) {
        renderEmpty(list, "Your pantry is empty. Add an ingredient above.");
        return;
    }

    items.forEach(item => {
        const row = document.createElement("div");
        row.className = "item-row";

        const main = document.createElement("div");
        main.className = "item-main";

        const name = document.createElement("div");
        name.className = "item-name";
        name.textContent = item.name || "Unnamed ingredient";

        const meta = document.createElement("div");
        meta.className = "item-meta";
        meta.textContent = [
            formatQuantity(item),
            item.expires_on ? `Expires ${item.expires_on}` : ""
        ].filter(Boolean).join(" · ");

        main.append(name, meta);

        const button = document.createElement("button");
        button.className = "button button-light";
        button.textContent = "Use";
        button.type = "button";
        button.addEventListener("click", () => useItem(item));

        row.append(main, button);
        list.appendChild(row);
    });
}


async function refreshPantry() {
    const data = await callTool("list_pantry");
    const items = getArray(data, "pantry", "items");
    renderPantry(items);

    const preferences = data?.preferences || state.preferences || {};
    state.preferences = preferences;

    $("#diet-value").textContent = preferences.diet || "Not set";

    const dietInput = $("#diet");
    if (dietInput) {
        dietInput.value = preferences.diet || "";
    }

    const dislikesInput = $("#dislikes");
    if (dislikesInput) {
        dislikesInput.value = typeof preferences.dislikes === "string" ? preferences.dislikes : "";
    }

    await refreshExpiry();
    return items;
}

async function refreshExpiry() {
    try {
        const data = await callTool("expiring_soon", { days: 7 });
        const items = getArray(data, "items", "expiring", "pantry");
        renderExpiry(items);
        return items;
    } catch (error) {
        return [];
    }
}


function renderExpiry(items) {
    $("#expiry-count").textContent = items.length;

    const list = $("#expiry-list");
    list.innerHTML = "";

    if (!items.length) {
        renderEmpty(list, "No items reported as expiring soon.");
        return;
    }

    items.forEach(item => {
        const row = document.createElement("div");
        row.className = "item-row";

        const main = document.createElement("div");
        main.className = "item-main";

        const name = document.createElement("div");
        name.className = "item-name";
        name.textContent = item.name || item.item || "Ingredient";

        const meta = document.createElement("div");
        meta.className = "item-meta";
        meta.textContent = [
            item.expires_on ? `Expires ${item.expires_on}` : "",
            item.quantity != null ? formatQuantity(item) : ""
        ].filter(Boolean).join(" · ");

        const tag = document.createElement("span");
        tag.className = "item-tag warning";
        const left = item.days_left ?? item.days_until_expiry ?? item.days;
        tag.textContent = left == null
            ? "Check"
            : left < 0
                ? "Expired"
                : left === 0
                    ? "Expires today"
                    : `${left} day${left === 1 ? "" : "s"} left`;

        main.append(name, meta);
        row.append(main, tag);
        list.appendChild(row);
    });
}

function renderMeals(meals) {
    state.meals = meals;

    const list = $("#meal-list");
    list.innerHTML = "";

    if (!meals.length) {
        renderEmpty(list, "No meal suggestions were returned.");
        return;
    }

    meals.forEach((meal, index) => {
        const card = document.createElement("div");
        card.className = "meal-card";

        const title = document.createElement("h3");
        title.textContent = meal.name || meal.title || `Meal ${index + 1}`;

        const description = document.createElement("p");
        description.textContent =
            meal.description ||
            meal.reason ||
            (meal.minutes ? `Ready in about ${meal.minutes} minutes.` : "Suggested for your kitchen.");

        card.append(title, description);

        const ingredients = meal.missing ||
            meal.missing_ingredients ||
            meal.missingIngredients;

        const missing = document.createElement("p");
        missing.textContent = Array.isArray(ingredients) && ingredients.length
            ? `Shopping needed: ${ingredients.join(", ")}`
            : "You have everything for this one.";
        card.appendChild(missing);

        const button = document.createElement("button");
        button.type = "button";
        button.className = "button button-light";
        button.textContent = "Add to shopping list";
        button.addEventListener("click", async () => {
            const id = meal.id || meal.recipe_id || meal.name;
            state.shoppingRecipeIds = [...new Set([...state.shoppingRecipeIds, id])];
            try {
                await buildShoppingList();
            } catch (error) {
                showMessage(error.message || "Couldn't build the shopping list.", true);
            }
        });

        card.appendChild(button);
        list.appendChild(card);
    });
}

function renderShoppingList(data) {
    const list = $("#shopping-list");
    list.innerHTML = "";

    const items = getArray(
        data,
        "list",
        "items",
        "shopping_list",
        "shoppingList"
    );
    if (items.length) {
        items.forEach(item => {
            const row = document.createElement("div");
            row.className = "item-row";

            const main = document.createElement("div");
            main.className = "item-main";

            const name = document.createElement("div");
            name.className = "item-name";
            name.textContent = typeof item === "string"
                ? item
                : item.name || item.item || "Shopping item";

            const meta = document.createElement("div");
            meta.className = "item-meta";
            meta.textContent = typeof item === "string"
                ? ""
                : formatQuantity(item);

            main.append(name, meta);
            row.appendChild(main);
            list.appendChild(row);
        });
        return;
    }

    if (typeof data === "string" && data.trim()) {
        const p = document.createElement("p");
        p.className = "item-meta";
        p.textContent = data;
        list.appendChild(p);
        return;
    }

    renderEmpty(list, "No shopping items were returned.");
}

async function buildShoppingList() {
    let ids = state.shoppingRecipeIds;

    if (!ids.length) {
        if (!state.meals.length) {
            const suggested = await callTool("suggest_meals", { days: 3 });
            renderMeals(getArray(suggested, "meals", "suggestions", "recipes"));
        }
        ids = state.meals.map(meal => meal.id).filter(Boolean);
    }

    if (!ids.length) {
        renderEmpty($("#shopping-list"), "No meals match your preferences yet.");
        showMessage("No meals to build a list from. Try changing your food preference.");
        return;
    }

    const data = await callTool("build_shopping_list", { recipe_ids: ids });
    renderShoppingList(data);

    const count = getArray(data, "list", "items").length;
    showMessage(count
        ? `Shopping list ready: ${count} item(s) to buy.`
        : "You already have everything for those meals.");
}

async function useItem(item) {
    const answer = prompt(
        `How much ${item.name} did you use?`,
        String(item.quantity ?? 1)
    );
    if (answer === null) return;
    const quantity = Number(answer);

    if (!Number.isFinite(quantity) || quantity <= 0) {
        showMessage("Enter a valid positive quantity.", true);
        return;
    }

    try {
        await callTool("use_pantry_item", {
            name: item.name,
            quantity
        });

        await refreshPantry();
        showMessage(`${item.name} updated.`);
    } catch (error) {
        showMessage(`Couldn't update ingredient: ${error.message}`, true);
    }
}

async function loadTools() {
    const result = await mcpRequest("tools/list");
    state.tools = result.tools || [];
}

async function runAction(action, task) {
    const button = $(action);
    const oldText = button.textContent;

    button.disabled = true;
    button.textContent = "Working...";

    try {
        await task();
    } catch (error) {
        showMessage(error.message || "Something went wrong.", true);
    } finally {
        button.disabled = false;
        button.textContent = oldText;
    }
}

$("#refresh-pantry").addEventListener("click", () =>
    runAction("#refresh-pantry", async () => {
        await refreshPantry();
        showMessage("Pantry refreshed.");
    })
);

$("#add-item-form").addEventListener("submit", event => {
    event.preventDefault();
    const formElement = event.currentTarget; // keep a reference: currentTarget is null after any await

    runAction("#add-item-form button[type='submit']", async () => {
        const form = new FormData(formElement);
        const name = String(form.get("name") || "").trim();
        const quantity = Number(form.get("quantity"));
        const unit = String(form.get("unit") || "pieces");
        const expires_on = String(form.get("expires_on") || "");

        if (!name || !Number.isFinite(quantity) || quantity <= 0) {
            throw new Error("Enter an ingredient name and a valid quantity.");
        }

        const args = { name, quantity, unit };
        if (expires_on) args.expires_on = expires_on;

        await callTool("add_pantry_item", args);
        formElement.reset();
        $("#item-quantity").value = "1";

        await refreshPantry();
        showMessage(`${name} added to your pantry.`);
    });
});

$("#check-expiry").addEventListener("click", () =>
    runAction("#check-expiry", async () => {
        const items = await refreshExpiry();
        showMessage(items.length
            ? `${items.length} item(s) expiring within 7 days.`
            : "Nothing is expiring in the next 7 days.");
    })
);

$("#suggest-meals").addEventListener("click", () =>
    runAction("#suggest-meals", async () => {
        const data = await callTool("suggest_meals", { days: 4 });
        const meals = getArray(data, "meals", "suggestions", "recipes");
        renderMeals(meals);
        showMessage(`Received ${meals.length} meal suggestion(s).`);
    })
);

$("#build-shopping-list").addEventListener("click", () =>
    runAction("#build-shopping-list", buildShoppingList)
);

$("#preference-form").addEventListener("submit", event => {
    event.preventDefault();

    runAction("#preference-form button[type='submit']", async () => {
        const diet = $("#diet").value;
        const dislikes = $("#dislikes").value
            .split(",")
            .map(value => value.trim())
            .filter(Boolean)
            .join(", ");

        if (diet) {
            await callTool("remember_preference", { key: "diet", value: diet });
        }
        await callTool("remember_preference", { key: "dislikes", value: dislikes });

        // Preferences changed, so earlier meal suggestions are stale.
        state.meals = [];
        state.shoppingRecipeIds = [];
        await refreshPantry();
        showMessage("Your food preference was saved. Tap Suggest meals to refresh ideas.");
    });
});

async function initialise() {
    try {
        showMessage("Connecting to your PantryPilot server...");

        await loadTools();

        const requiredTools = [
            "add_pantry_item",
            "use_pantry_item",
            "list_pantry",
            "expiring_soon",
            "remember_preference",
            "suggest_meals",
            "build_shopping_list"
        ];

        const available = new Set(state.tools.map(tool => tool.name));
        const missing = requiredTools.filter(name => !available.has(name));

        if (missing.length) {
            throw new Error(`Missing backend tools: ${missing.join(", ")}`);
        }

        await refreshPantry();
        showMessage("Connected to PantryPilot. Your data is loaded.");
    } catch (error) {
        showMessage(
            `Couldn't connect: ${error.message}. Make sure the PantryPilot server is running.`,
            true
        );
    }
}

initialise();
