document.addEventListener('DOMContentLoaded', function() {
    // Проверяем, есть ли товары на странице
    const tbody = document.getElementById('products-tbody');
    if (!tbody) {
        console.log('Нет данных о товарах для отображения графиков');
        return;
    }

    const table = document.getElementById('products-table');
    const productsCount = document.getElementById('products-count');
    const filteredCount = document.getElementById('filtered-count');
    const averagePrice = document.getElementById('average-price');
    const averageRating = document.getElementById('average-rating');
    const averageDiscount = document.getElementById('average-discount');

    // Элементы фильтров
    const priceFrom = document.getElementById('price-from');
    const priceTo = document.getElementById('price-to');
    const ratingFilter = document.getElementById('rating-filter');
    const reviewsFilter = document.getElementById('reviews-filter');
    const sortBy = document.getElementById('sort-by');
    const sortOrder = document.getElementById('sort-order');
    const resetButton = document.getElementById('reset-filters');

    // Все строки таблицы
    let allRows = Array.from(tbody.querySelectorAll('tr'));
    console.log(`Загружено ${allRows.length} товаров`);

    // Проверяем, есть ли данные
    if (allRows.length === 0) {
        console.log('Нет строк с товарами для анализа');
        return;
    }

    // Графики
    let priceHistogramChart = null;
    let discountRatingChart = null;

    // Инициализация графиков
    function initCharts() {
        try {
            // Гистограмма цен
            const priceCanvas = document.getElementById('price-histogram');
            if (!priceCanvas) {
                console.error('Не найден canvas для гистограммы цен');
                return;
            }

            const priceCtx = priceCanvas.getContext('2d');
            priceHistogramChart = new Chart(priceCtx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Количество товаров',
                        data: [],
                        backgroundColor: 'rgba(102, 126, 234, 0.8)',
                        borderColor: 'rgba(102, 126, 234, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Диапазон цен (₽)'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: 'Распределение товаров по ценам'
                        }
                    }
                }
            });

            // График скидка vs рейтинг
            const discountCanvas = document.getElementById('discount-rating-chart');
            if (!discountCanvas) {
                console.error('Не найден canvas для графика скидок');
                return;
            }

            const discountCtx = discountCanvas.getContext('2d');
            discountRatingChart = new Chart(discountCtx, {
                type: 'scatter',
                data: {
                    datasets: [{
                        label: 'Товары',
                        data: [],
                        backgroundColor: function(context) {
                            if (!context.parsed) return 'rgba(108, 117, 125, 0.7)';
                            const discount = context.parsed.y;
                            if (discount >= 50) return 'rgba(220, 53, 69, 0.7)';
                            if (discount >= 30) return 'rgba(255, 193, 7, 0.7)';
                            if (discount >= 10) return 'rgba(40, 167, 69, 0.7)';
                            return 'rgba(108, 117, 125, 0.7)';
                        },
                        borderColor: function(context) {
                            if (!context.parsed) return 'rgba(108, 117, 125, 1)';
                            const discount = context.parsed.y;
                            if (discount >= 50) return 'rgba(220, 53, 69, 1)';
                            if (discount >= 30) return 'rgba(255, 193, 7, 1)';
                            if (discount >= 10) return 'rgba(40, 167, 69, 1)';
                            return 'rgba(108, 117, 125, 1)';
                        },
                        borderWidth: 1,
                        pointRadius: 5,
                        pointHoverRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Рейтинг товара ⭐'
                            },
                            min: 0,
                            max: 5,
                            ticks: {
                                stepSize: 0.5
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Размер скидки (%)'
                            },
                            min: 0,
                            ticks: {
                                callback: function(value) {
                                    return value + '%';
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: 'Зависимость размера скидки от рейтинга товара',
                            font: {
                                size: 14
                            }
                        },
                        tooltip: {
                            callbacks: {
                                title: function(context) {
                                    const dataIndex = context[0].dataIndex;
                                    if (dataIndex < allRows.length) {
                                        const row = allRows[dataIndex];
                                        const name = row.dataset.name || '';
                                        return name.substring(0, 50) + (name.length > 50 ? '...' : '');
                                    }
                                    return '';
                                },
                                label: function(context) {
                                    const dataIndex = context.dataIndex;
                                    if (dataIndex < allRows.length) {
                                        const row = allRows[dataIndex];
                                        const rating = parseFloat(row.dataset.rating) || 0;
                                        const discount = context.parsed.y;
                                        const reviews = parseInt(row.dataset.reviews) || 0;
                                        const priceWithDiscount = parseFloat(row.dataset.priceWithDiscount) || 0;

                                        return [
                                            `Рейтинг: ${rating.toFixed(1)} ⭐`,
                                            `Скидка: ${discount.toFixed(1)}%`,
                                            `Отзывы: ${reviews}`,
                                            `Цена: ${priceWithDiscount.toLocaleString('ru-RU')} ₽`
                                        ];
                                    }
                                    return '';
                                }
                            }
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'point'
                    }
                }
            });

            console.log('Графики инициализированы успешно');
        } catch (error) {
            console.error('Ошибка при инициализации графиков:', error);
        }
    }

    // Обновление гистограммы цен
    function updatePriceHistogram(rows) {
        if (!priceHistogramChart) return;

        const prices = rows.map(row => {
            return parseFloat(row.dataset.priceWithDiscount) || parseFloat(row.dataset.priceNoDiscount) || 0;
        }).filter(price => price > 0);

        console.log(`Обновление гистограммы цен для ${prices.length} товаров`);

        if (prices.length === 0) {
            priceHistogramChart.data.labels = ['Нет данных'];
            priceHistogramChart.data.datasets[0].data = [0];
            priceHistogramChart.update();
            return;
        }

        // Создаем диапазоны цен
        const minPrice = Math.min(...prices);
        const maxPrice = Math.max(...prices);
        const range = maxPrice - minPrice;

        if (range === 0) {
            priceHistogramChart.data.labels = [`${Math.round(minPrice)} ₽`];
            priceHistogramChart.data.datasets[0].data = [prices.length];
            priceHistogramChart.update();
            return;
        }

        const binCount = Math.min(10, Math.max(5, Math.ceil(Math.sqrt(prices.length))));
        const binSize = range / binCount;

        const bins = [];
        const labels = [];

        for (let i = 0; i < binCount; i++) {
            const binStart = minPrice + (i * binSize);
            const binEnd = minPrice + ((i + 1) * binSize);

            bins.push(0);
            if (i === binCount - 1) {
                labels.push(`${Math.round(binStart)}-${Math.round(binEnd)}`);
            } else {
                labels.push(`${Math.round(binStart)}-${Math.round(binEnd - 1)}`);
            }
        }

        // Подсчитываем товары в каждом диапазоне
        prices.forEach(price => {
            let binIndex = Math.floor((price - minPrice) / binSize);
            if (binIndex >= binCount) binIndex = binCount - 1;
            if (binIndex < 0) binIndex = 0;
            bins[binIndex]++;
        });

        priceHistogramChart.data.labels = labels;
        priceHistogramChart.data.datasets[0].data = bins;
        priceHistogramChart.update();
    }

    // Обновление графика скидка vs рейтинг
    function updateDiscountRatingChart(rows) {
        if (!discountRatingChart) return;

        const data = [];

        rows.forEach((row, index) => {
            const priceNoDiscount = parseFloat(row.dataset.priceNoDiscount) || 0;
            const priceWithDiscount = parseFloat(row.dataset.priceWithDiscount) || 0;
            const rating = parseFloat(row.dataset.rating) || 0;

            if (priceNoDiscount > 0 && priceWithDiscount > 0 && rating > 0 && priceNoDiscount > priceWithDiscount) {
                const discount = ((priceNoDiscount - priceWithDiscount) / priceNoDiscount) * 100;
                if (discount >= 0) {
                    data.push({
                        x: rating,
                        y: discount
                    });
                }
            }
        });

        console.log(`Обновление графика скидок для ${data.length} товаров со скидками`);

        discountRatingChart.data.datasets[0].data = data;
        discountRatingChart.update();
    }

    // Обновление графиков
    function updateCharts(rows) {
        updatePriceHistogram(rows);
        updateDiscountRatingChart(rows);
    }

    // Фильтрация товаров
    function filterProducts() {
        const minPrice = parseFloat(priceFrom.value) || 0;
        const maxPrice = parseFloat(priceTo.value) || 1000000;
        const minRating = parseFloat(ratingFilter.value);
        const minReviews = parseInt(reviewsFilter.value);

        const filteredRows = allRows.filter(row => {
            const price = parseFloat(row.dataset.priceWithDiscount) || parseFloat(row.dataset.priceNoDiscount) || 0;
            const rating = parseFloat(row.dataset.rating) || 0;
            const reviews = parseInt(row.dataset.reviews) || 0;

            return price >= minPrice &&
                   price <= maxPrice &&
                   rating >= minRating &&
                   reviews >= minReviews;
        });

        return filteredRows;
    }

    // Сортировка товаров
    function sortProducts(rows) {
        const sortField = sortBy.value;
        const isAsc = sortOrder.value === 'asc';

        return rows.sort((a, b) => {
            let valueA, valueB;

            switch (sortField) {
                case 'name':
                    valueA = a.dataset.name.toLowerCase();
                    valueB = b.dataset.name.toLowerCase();
                    break;
                case 'price_no_discounts':
                    valueA = parseFloat(a.dataset.priceNoDiscount) || 0;
                    valueB = parseFloat(b.dataset.priceNoDiscount) || 0;
                    break;
                case 'price_with_discount':
                    valueA = parseFloat(a.dataset.priceWithDiscount) || 0;
                    valueB = parseFloat(b.dataset.priceWithDiscount) || 0;
                    break;
                case 'rating':
                    valueA = parseFloat(a.dataset.rating) || 0;
                    valueB = parseFloat(b.dataset.rating) || 0;
                    break;
                case 'number_of_reviews':
                    valueA = parseInt(a.dataset.reviews) || 0;
                    valueB = parseInt(b.dataset.reviews) || 0;
                    break;
                default:
                    return 0;
            }

            if (valueA < valueB) return isAsc ? -1 : 1;
            if (valueA > valueB) return isAsc ? 1 : -1;
            return 0;
        });
    }

    // Обновление статистики
    function updateStatistics(rows) {
        filteredCount.textContent = rows.length;

        const prices = rows.map(row => {
            return parseFloat(row.dataset.priceWithDiscount) || parseFloat(row.dataset.priceNoDiscount) || 0;
        }).filter(price => price > 0);

        const ratings = rows.map(row => parseFloat(row.dataset.rating) || 0).filter(rating => rating > 0);

        // Подсчет скидок
        const discounts = [];
        rows.forEach(row => {
            const priceNoDiscount = parseFloat(row.dataset.priceNoDiscount) || 0;
            const priceWithDiscount = parseFloat(row.dataset.priceWithDiscount) || 0;

            if (priceNoDiscount > 0 && priceWithDiscount > 0 && priceNoDiscount > priceWithDiscount) {
                const discount = ((priceNoDiscount - priceWithDiscount) / priceNoDiscount) * 100;
                discounts.push(discount);
            }
        });

        if (prices.length > 0) {
            const avgPrice = prices.reduce((sum, price) => sum + price, 0) / prices.length;
            averagePrice.textContent = avgPrice.toLocaleString('ru-RU', {minimumFractionDigits: 2, maximumFractionDigits: 2}) + ' ₽';
        } else {
            averagePrice.textContent = '-';
        }

        if (ratings.length > 0) {
            const avgRating = ratings.reduce((sum, rating) => sum + rating, 0) / ratings.length;
            averageRating.textContent = '⭐ ' + avgRating.toFixed(1);
        } else {
            averageRating.textContent = '-';
        }

        if (discounts.length > 0) {
            const avgDiscount = discounts.reduce((sum, discount) => sum + discount, 0) / discounts.length;
            averageDiscount.textContent = avgDiscount.toFixed(1) + '%';
        } else {
            averageDiscount.textContent = '0%';
        }
    }

    // Обновление таблицы
    function updateTable() {
        const filteredRows = filterProducts();
        const sortedRows = sortProducts(filteredRows);

        // Очищаем tbody
        tbody.innerHTML = '';

        // Добавляем отфильтрованные и отсортированные строки
        sortedRows.forEach((row, index) => {
            const rowNumber = row.querySelector('.row-number');
            rowNumber.textContent = index + 1;
            tbody.appendChild(row);
        });

        updateStatistics(sortedRows);
        updateCharts(sortedRows);
    }

    // Валидация полей цен
    function validatePriceInputs() {
        const fromValue = parseFloat(priceFrom.value) || 0;
        const toValue = parseFloat(priceTo.value) || 1000000;

        if (fromValue > toValue) {
            priceFrom.value = toValue;
        }

        if (fromValue < 0) {
            priceFrom.value = 0;
        }

        if (toValue < 0) {
            priceTo.value = 0;
        }
    }

    // Сброс фильтров
    function resetFilters() {
        priceFrom.value = 0;
        priceTo.value = 1000000;
        ratingFilter.value = '0';
        reviewsFilter.value = '0';
        sortBy.value = 'name';
        sortOrder.value = 'asc';
        updateTable();
    }

    // События для полей цен
    priceFrom.addEventListener('input', function() {
        validatePriceInputs();
        updateTable();
    });

    priceFrom.addEventListener('blur', function() {
        if (this.value === '') {
            this.value = 0;
        }
        validatePriceInputs();
        updateTable();
    });

    priceTo.addEventListener('input', function() {
        validatePriceInputs();
        updateTable();
    });

    priceTo.addEventListener('blur', function() {
        if (this.value === '') {
            this.value = 1000000;
        }
        validatePriceInputs();
        updateTable();
    });

    // Остальные события
    ratingFilter.addEventListener('change', updateTable);
    reviewsFilter.addEventListener('change', updateTable);
    sortBy.addEventListener('change', updateTable);
    sortOrder.addEventListener('change', updateTable);
    resetButton.addEventListener('click', resetFilters);

    // Инициализация
    initCharts();
    updateTable();
});