package com.vulnmno.app.ui.screens.shop

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.navigation.NavHostController
import com.vulnmno.app.data.remote.dto.*
import com.vulnmno.app.data.repository.*
import com.vulnmno.app.ui.navigation.Routes
import com.vulnmno.app.ui.screens.ErrorBox
import com.vulnmno.app.ui.screens.LoadingBox
import com.vulnmno.app.ui.screens.userMessage
import dagger.hilt.android.lifecycle.HiltViewModel
import java.util.UUID
import javax.inject.Inject
import kotlinx.coroutines.async
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

// ---------- Shop ----------

@HiltViewModel
class ShopViewModel @Inject constructor(private val repo: ShopRepository) : ViewModel() {
    data class S(val items: List<ProductDto> = emptyList(), val loading: Boolean = true, val err: String? = null)
    private val _s = MutableStateFlow(S()); val s: StateFlow<S> = _s.asStateFlow()
    init { load() }
    fun load() = viewModelScope.launch {
        _s.update { it.copy(loading = true, err = null) }
        _s.value = when (val r = repo.products()) {
            is ApiResult.Ok -> S(items = r.value.items, loading = false)
            is ApiResult.Err -> S(loading = false, err = r.error.userMessage())
        }
    }
}

@Composable
fun ShopScreen(nav: NavHostController, vm: ShopViewModel = hiltViewModel()) {
    val s = vm.s.collectAsState().value
    when {
        s.loading -> LoadingBox()
        s.err != null -> ErrorBox(s.err, true, vm::load)
        s.items.isEmpty() -> ErrorBox("No products available.", retryable = true, onRetry = vm::load)
        else -> LazyColumn(Modifier.fillMaxSize().padding(16.dp)) {
            items(s.items) { p ->
                ElevatedCard(
                    onClick = { nav.navigate(Routes.product(p.productId)) },
                    modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                ) {
                    Column(Modifier.padding(16.dp)) {
                        Text(p.name, style = MaterialTheme.typography.titleSmall)
                        Text("${p.price} ${p.currency}")
                        p.description?.let { Text(it, style = MaterialTheme.typography.bodySmall) }
                    }
                }
            }
        }
    }
}

// ---------- Product detail ----------

@HiltViewModel
class ProductDetailViewModel @Inject constructor(private val repo: ShopRepository) : ViewModel() {
    sealed interface S { data object Loading : S; data class Loaded(val p: ProductDto) : S; data class Err(val msg: String) : S }
    private val _s = MutableStateFlow<S>(S.Loading); val s: StateFlow<S> = _s.asStateFlow()
    fun load(id: String) = viewModelScope.launch {
        _s.value = when (val r = repo.product(id)) {
            is ApiResult.Ok -> S.Loaded(r.value); is ApiResult.Err -> S.Err(r.error.userMessage())
        }
    }
}

@Composable
fun ProductDetailScreen(nav: NavHostController, productId: String, vm: ProductDetailViewModel = hiltViewModel()) {
    LaunchedEffect(productId) { vm.load(productId) }
    when (val s = vm.s.collectAsState().value) {
        ProductDetailViewModel.S.Loading -> LoadingBox()
        is ProductDetailViewModel.S.Err -> ErrorBox(s.msg)
        is ProductDetailViewModel.S.Loaded -> Column(Modifier.fillMaxSize().padding(16.dp)) {
            Text(s.p.name, style = MaterialTheme.typography.titleLarge)
            s.p.description?.let { Text(it) }
            Spacer(Modifier.height(16.dp))
            Text("${s.p.price} ${s.p.currency}", style = MaterialTheme.typography.headlineSmall)
            Spacer(Modifier.height(8.dp))
            Text("Validity: ${s.p.validityDays ?: "—"} days")
            Text("Eligible plans: ${s.p.eligiblePlans.joinToString().ifBlank { "all" }}")
            Spacer(Modifier.weight(1f))
            Button(onClick = { nav.navigate(Routes.checkout(s.p.productId)) }, modifier = Modifier.fillMaxWidth()) {
                Text("Buy")
            }
        }
    }
}

// ---------- Checkout ----------

@HiltViewModel
class CheckoutViewModel @Inject constructor(
    private val shop: ShopRepository,
    private val accounts: AccountsRepository,
) : ViewModel() {
    sealed interface PromoStatus {
        data object NotApplied : PromoStatus
        data object Applying : PromoStatus
        data class Applied(val promo: PromoApplicationDto) : PromoStatus
        data class Invalid(val msg: String) : PromoStatus
        data class Ineligible(val rule: String?) : PromoStatus
    }
    data class S(
        val product: ProductDto? = null,
        val balance: BalanceDto? = null,
        val promoCode: String = "",
        val promo: PromoStatus = PromoStatus.NotApplied,
        val purchasing: Boolean = false,
        val error: String? = null,
        val purchaseId: String? = null,
    )
    private val _s = MutableStateFlow(S()); val s: StateFlow<S> = _s.asStateFlow()
    fun load(productId: String) = viewModelScope.launch {
        val p = async { shop.product(productId) }; val b = async { accounts.balance() }
        _s.update {
            it.copy(product = (p.await() as? ApiResult.Ok)?.value, balance = (b.await() as? ApiResult.Ok)?.value)
        }
    }
    fun onPromoChange(v: String) = _s.update { it.copy(promoCode = v, promo = PromoStatus.NotApplied) }
    fun applyPromo() = viewModelScope.launch {
        val st = _s.value; val product = st.product ?: return@launch
        if (st.promoCode.isBlank()) return@launch
        _s.update { it.copy(promo = PromoStatus.Applying) }
        _s.update {
            it.copy(promo = when (val r = shop.applyPromo(product.productId, st.promoCode)) {
                is ApiResult.Ok -> PromoStatus.Applied(r.value)
                is ApiResult.Err -> {
                    val d = r.error as? com.vulnmno.app.data.remote.AppError.Domain
                    when (d?.code) {
                        "PROMO_INELIGIBLE" -> PromoStatus.Ineligible(d.rule)
                        "PROMO_INVALID" -> PromoStatus.Invalid(d.message)
                        else -> PromoStatus.Invalid(r.error.userMessage())
                    }
                }
            })
        }
    }
    fun confirm(idempotencyKey: String) = viewModelScope.launch {
        val st = _s.value; val product = st.product ?: return@launch
        _s.update { it.copy(purchasing = true, error = null) }
        val code = if (st.promo is PromoStatus.Applied) st.promoCode else null
        _s.update {
            when (val r = shop.purchase(idempotencyKey, product.productId, code)) {
                is ApiResult.Ok -> it.copy(purchasing = false, purchaseId = r.value.purchaseId)
                is ApiResult.Err -> it.copy(purchasing = false, error = r.error.userMessage())
            }
        }
    }
}

@Composable
fun CheckoutScreen(nav: NavHostController, productId: String, vm: CheckoutViewModel = hiltViewModel()) {
    LaunchedEffect(productId) { vm.load(productId) }
    val s = vm.s.collectAsState().value
    val idempotencyKey = rememberSaveable { UUID.randomUUID().toString() }
    LaunchedEffect(s.purchaseId) {
        s.purchaseId?.let {
            nav.navigate(Routes.purchaseConfirmation(it)) {
                popUpTo(Routes.shop) { inclusive = false }
            }
        }
    }
    val product = s.product
    if (product == null) { LoadingBox(); return }
    val finalPrice = (s.promo as? CheckoutViewModel.PromoStatus.Applied)?.promo?.finalPrice ?: product.price
    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Text(product.name, style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(8.dp))
        Text("Original: ${product.price} ${product.currency}")
        Text("Wallet: ${s.balance?.balance ?: "—"} ${product.currency}")
        Spacer(Modifier.height(16.dp))
        OutlinedTextField(
            value = s.promoCode, onValueChange = vm::onPromoChange,
            label = { Text("Promo code") }, modifier = Modifier.fillMaxWidth(),
        )
        Spacer(Modifier.height(4.dp))
        OutlinedButton(onClick = { vm.applyPromo() }, enabled = s.promo !is CheckoutViewModel.PromoStatus.Applying && s.promoCode.isNotBlank()) {
            Text("Apply promo")
        }
        when (val ps = s.promo) {
            is CheckoutViewModel.PromoStatus.Applied -> Text("Discount: ${ps.promo.discountAmount}")
            is CheckoutViewModel.PromoStatus.Invalid -> Text(ps.msg, color = MaterialTheme.colorScheme.error)
            is CheckoutViewModel.PromoStatus.Ineligible -> Text("Not eligible: ${ps.rule ?: "rule not specified"}", color = MaterialTheme.colorScheme.error)
            else -> Unit
        }
        Spacer(Modifier.height(16.dp))
        Text("Final: $finalPrice ${product.currency}", style = MaterialTheme.typography.headlineSmall)
        Spacer(Modifier.weight(1f))
        s.error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        Button(onClick = { vm.confirm(idempotencyKey) }, enabled = !s.purchasing, modifier = Modifier.fillMaxWidth()) {
            Text(if (s.purchasing) "Processing…" else "Confirm purchase")
        }
    }
}

// ---------- Purchase confirmation ----------

@Composable
fun PurchaseConfirmationScreen(nav: NavHostController, purchaseId: String) {
    Column(Modifier.fillMaxSize().padding(24.dp), verticalArrangement = Arrangement.Center) {
        Text("Purchase confirmed", style = MaterialTheme.typography.headlineSmall)
        Spacer(Modifier.height(8.dp))
        Text("Reference: $purchaseId")
        Spacer(Modifier.height(24.dp))
        Button(onClick = {
            nav.popBackStack(Routes.shop, inclusive = false)
        }, modifier = Modifier.fillMaxWidth()) { Text("Done") }
    }
}
