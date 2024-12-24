// $(document).ready(function() {
//     loadProducts(); // Load products when the page is ready
//     initializeCart(); // Initialize the cart
// });

// let cart = [];

// function initializeCart() {
//     // Load cart from local storage if available
//     const storedCart = localStorage.getItem('cart');
//     if (storedCart) {
//         cart = JSON.parse(storedCart);
//     }
//     updateCartDisplay();
// }

// function loadProducts() {
//     $.ajax({
//         url: '/pos_products', // Endpoint to fetch products
//         type: 'GET',
//         success: function(products) {
//             renderProducts(products);
//         },
//         error: function(error) {
//             console.error('Error fetching products:', error);
//         }
//     });
// }

// function renderProducts(products) {
//     const parentElement = $('#parent');
//     parentElement.empty(); // Clear existing products

//     products.forEach(product => {
//         const productCard = `
//             <div class="col-md-3 mb-4">
//                 <div class="card h-100">
//                     <img class="card-img-top" src="/static/uploads/product/original/${product.image}" alt="${product.product_name}" style="width: 100%; object-fit: cover;">
//                     <div class="card-body">
//                         <h5 class="card-title">${product.product_name}</h5>
//                         <p class="card-text">Price: $${parseFloat(product.price).toFixed(2)}</p>
//                         <button class="btn btn-primary" onclick="addToCart(${product.id}, '${product.product_name}', ${product.price})">Add to Cart</button>
//                     </div>
//                 </div>
//             </div>
//         `;
//         parentElement.append(productCard);
//     });
// }

// function addToCart(productId, productName, productPrice) {
//     const existingProduct = cart.find(item => item.id === productId);
//     if (existingProduct) {
//         existingProduct.quantity += 1;
//     } else {
//         cart.push({ id: productId, name: productName, price: productPrice, quantity: 1 });
//     }
//     localStorage.setItem('cart', JSON.stringify(cart)); // Save cart to local storage
//     updateCartDisplay();
//     console.log('Product added to cart:', productId);
// }

// function updateCartDisplay() {
//     const cartElement = $('#cart');
//     cartElement.empty();
//     cart.forEach(item => {
//         cartElement.append(`<li>${item.name} - Quantity: ${item.quantity}</li>`);
//     });
// }


