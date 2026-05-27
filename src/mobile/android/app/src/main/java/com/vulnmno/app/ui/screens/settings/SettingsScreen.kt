package com.vulnmno.app.ui.screens.settings

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.navigation.NavHostController
import com.vulnmno.app.data.remote.dto.AddressDto
import com.vulnmno.app.data.remote.dto.ContactDetailsUpdateDto
import com.vulnmno.app.data.remote.dto.CustomerDto
import com.vulnmno.app.data.remote.dto.NotificationPreferencesDto
import com.vulnmno.app.data.remote.dto.NotificationPreferencesUpdateDto
import com.vulnmno.app.data.repository.ApiResult
import com.vulnmno.app.data.repository.CustomerRepository
import com.vulnmno.app.data.repository.NotificationsRepository
import com.vulnmno.app.ui.navigation.AuthGate
import com.vulnmno.app.ui.navigation.AuthIntent
import com.vulnmno.app.ui.navigation.Routes
import com.vulnmno.app.ui.screens.ErrorBox
import com.vulnmno.app.ui.screens.LoadingBox
import com.vulnmno.app.ui.screens.userMessage
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val customers: CustomerRepository,
    private val notifications: NotificationsRepository,
) : ViewModel() {

    data class S(
        val loading: Boolean = true,
        val err: String? = null,
        val customer: CustomerDto? = null,
        val prefs: NotificationPreferencesDto = NotificationPreferencesDto(
            push = true, sms = true, email = true, inApp = true,
        ),
        val savingPrefs: Boolean = false,
        val savingContact: Boolean = false,
        val flash: String? = null,
    )

    private val _s = MutableStateFlow(S())
    val s: StateFlow<S> = _s.asStateFlow()
    fun consumeFlash() { _s.update { it.copy(flash = null) } }

    fun load() = viewModelScope.launch {
        _s.update { it.copy(loading = true, err = null) }
        when (val r = customers.me()) {
            is ApiResult.Ok -> _s.update {
                it.copy(
                    loading = false,
                    customer = r.value,
                    // Preserve current toggles when the server provides them; fall back to all-on
                    // (matches the seed default) when notificationPreferences is missing.
                    prefs = r.value.notificationPreferences ?: it.prefs,
                )
            }
            is ApiResult.Err -> _s.update { it.copy(loading = false, err = r.error.userMessage()) }
        }
    }

    fun togglePref(field: PrefField, value: Boolean) = viewModelScope.launch {
        _s.update { it.copy(savingPrefs = true) }
        val patch = when (field) {
            PrefField.PUSH  -> NotificationPreferencesUpdateDto(push = value)
            PrefField.SMS   -> NotificationPreferencesUpdateDto(sms = value)
            PrefField.EMAIL -> NotificationPreferencesUpdateDto(email = value)
            PrefField.INAPP -> NotificationPreferencesUpdateDto(inApp = value)
        }
        when (val r = notifications.updatePrefs(patch)) {
            is ApiResult.Ok -> _s.update { it.copy(savingPrefs = false, prefs = r.value, flash = "Preferences updated") }
            is ApiResult.Err -> _s.update { it.copy(savingPrefs = false, err = r.error.userMessage()) }
        }
    }

    fun saveContactDetails(email: String?, address: AddressDto?) = viewModelScope.launch {
        _s.update { it.copy(savingContact = true) }
        val body = ContactDetailsUpdateDto(
            email = email?.takeIf { it.isNotBlank() },
            billingAddress = address,
        )
        when (val r = customers.updateContact(body)) {
            is ApiResult.Ok -> _s.update { it.copy(savingContact = false, customer = r.value, flash = "Contact details saved") }
            is ApiResult.Err -> _s.update { it.copy(savingContact = false, err = r.error.userMessage()) }
        }
    }

    enum class PrefField { PUSH, SMS, EMAIL, INAPP }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    nav: NavHostController,
    vm: SettingsViewModel = hiltViewModel(),
    gate: AuthGate = hiltViewModel(),
) {
    LaunchedEffect(Unit) { vm.load() }
    val s = vm.s.collectAsState().value
    val locale = LocalConfiguration.current.locales[0]?.toLanguageTag() ?: "—"

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Settings") },
                navigationIcon = {
                    IconButton(onClick = { if (!nav.popBackStack()) nav.navigate(Routes.home) { popUpTo(0) } }) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
            )
        }
    ) { pad ->
        when {
            s.loading -> Box(Modifier.padding(pad)) { LoadingBox() }
            s.err != null && s.customer == null -> ErrorBox(s.err, true, vm::load)
            s.customer != null -> Column(
                Modifier.padding(pad).fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp)
            ) {
                s.flash?.let {
                    LaunchedEffect(it) { kotlinx.coroutines.delay(2_500); vm.consumeFlash() }
                    Surface(color = MaterialTheme.colorScheme.secondaryContainer, modifier = Modifier.fillMaxWidth()) {
                        Text(it, modifier = Modifier.padding(12.dp), style = MaterialTheme.typography.bodyMedium)
                    }
                    Spacer(Modifier.height(12.dp))
                }

                // ---- Notifications section ----
                SectionTitle("Notifications")
                PrefSwitch("Push", s.prefs.push, s.savingPrefs) { vm.togglePref(SettingsViewModel.PrefField.PUSH, it) }
                PrefSwitch("SMS", s.prefs.sms, s.savingPrefs) { vm.togglePref(SettingsViewModel.PrefField.SMS, it) }
                PrefSwitch("Email", s.prefs.email, s.savingPrefs) { vm.togglePref(SettingsViewModel.PrefField.EMAIL, it) }
                PrefSwitch("In-app", s.prefs.inApp, s.savingPrefs) { vm.togglePref(SettingsViewModel.PrefField.INAPP, it) }

                Spacer(Modifier.height(24.dp))

                // ---- Contact details ----
                ContactSection(
                    customer = s.customer,
                    saving = s.savingContact,
                    onSave = vm::saveContactDetails,
                )

                Spacer(Modifier.height(24.dp))

                // ---- Language (read-only) ----
                SectionTitle("Language")
                ListItem(
                    headlineContent = { Text("Device language") },
                    supportingContent = { Text(locale) },
                    trailingContent = {
                        Text(
                            "Change in Android Settings",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    },
                )

                Spacer(Modifier.height(24.dp))

                // ---- Sign out ----
                OutlinedButton(
                    onClick = {
                        gate.onEvent(AuthIntent.Logout)
                    },
                    modifier = Modifier.fillMaxWidth(),
                ) { Text("Sign out") }
            }
        }
    }
}

@Composable
private fun SectionTitle(text: String) {
    Text(text, style = MaterialTheme.typography.titleMedium)
    Spacer(Modifier.height(8.dp))
}

@Composable
private fun PrefSwitch(label: String, checked: Boolean, saving: Boolean, onChange: (Boolean) -> Unit) {
    Row(
        Modifier.fillMaxWidth().padding(vertical = 4.dp),
        verticalAlignment = androidx.compose.ui.Alignment.CenterVertically,
    ) {
        Text(label, modifier = Modifier.weight(1f))
        Switch(checked = checked, onCheckedChange = onChange, enabled = !saving)
    }
}

@Composable
private fun ContactSection(
    customer: CustomerDto,
    saving: Boolean,
    onSave: (String?, AddressDto?) -> Unit,
) {
    var email by rememberSaveable(customer.email) { mutableStateOf(customer.email ?: "") }
    val addr = customer.billingAddress
    var line1 by rememberSaveable(addr?.line1) { mutableStateOf(addr?.line1 ?: "") }
    var city by rememberSaveable(addr?.city) { mutableStateOf(addr?.city ?: "") }
    var postalCode by rememberSaveable(addr?.postalCode) { mutableStateOf(addr?.postalCode ?: "") }
    var country by rememberSaveable(addr?.country) { mutableStateOf(addr?.country ?: "") }

    SectionTitle("Contact details")
    OutlinedTextField(
        value = email, onValueChange = { email = it }, label = { Text("Email") },
        singleLine = true, modifier = Modifier.fillMaxWidth(),
    )
    Spacer(Modifier.height(8.dp))
    OutlinedTextField(
        value = line1, onValueChange = { line1 = it }, label = { Text("Address line") },
        singleLine = true, modifier = Modifier.fillMaxWidth(),
    )
    Spacer(Modifier.height(8.dp))
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        OutlinedTextField(
            value = city, onValueChange = { city = it }, label = { Text("City") },
            singleLine = true, modifier = Modifier.weight(1f),
        )
        OutlinedTextField(
            value = postalCode, onValueChange = { postalCode = it }, label = { Text("Postal code") },
            singleLine = true, modifier = Modifier.weight(1f),
        )
    }
    Spacer(Modifier.height(8.dp))
    OutlinedTextField(
        value = country, onValueChange = { country = it.take(2).uppercase() }, label = { Text("Country (ISO-2)") },
        singleLine = true, modifier = Modifier.fillMaxWidth(),
    )
    Spacer(Modifier.height(12.dp))
    Button(
        onClick = {
            val nonEmpty = line1.isNotBlank() || city.isNotBlank() || postalCode.isNotBlank() || country.isNotBlank()
            val newAddr = if (nonEmpty) AddressDto(
                line1 = line1.ifBlank { null },
                city = city.ifBlank { null },
                postalCode = postalCode.ifBlank { null },
                country = country.ifBlank { null },
            ) else null
            onSave(email, newAddr)
        },
        enabled = !saving,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Text(if (saving) "Saving…" else "Save contact details")
    }
}
