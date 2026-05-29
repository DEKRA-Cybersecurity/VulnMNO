package com.vulnmno.app.ui.screens.auth

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.navigation.NavHostController
import com.vulnmno.app.data.local.BaseUrlStore
import com.vulnmno.app.data.repository.ApiResult
import com.vulnmno.app.data.repository.AuthRepository
import com.vulnmno.app.ui.navigation.AuthGate
import com.vulnmno.app.ui.navigation.Routes
import com.vulnmno.app.ui.screens.LoadingBox
import com.vulnmno.app.ui.screens.userMessage
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

@Composable
fun SplashScreen() { LoadingBox() }

// ---------- Login ----------

data class LoginUiState(
    val msisdn: String = "",
    val password: String = "",
    val submitting: Boolean = false,
    val formError: String? = null,
)

@HiltViewModel
class LoginViewModel @Inject constructor(
    private val authRepo: AuthRepository,
    private val baseUrlStore: BaseUrlStore,
) : ViewModel() {
    private val _state = MutableStateFlow(LoginUiState())
    val state: StateFlow<LoginUiState> = _state.asStateFlow()

    val baseUrlOverride: StateFlow<String?> = baseUrlStore.overrideFlow
        .stateIn(viewModelScope, SharingStarted.Eagerly, null)

    sealed interface Event { data class GoOtp(val token: String) : Event; data object LoggedIn : Event }
    private val _events = MutableStateFlow<Event?>(null)
    val events: StateFlow<Event?> = _events.asStateFlow()
    fun consume() { _events.value = null }

    fun onMsisdn(v: String) = _state.update { it.copy(msisdn = v, formError = null) }
    fun onPassword(v: String) = _state.update { it.copy(password = v, formError = null) }

    fun setBaseUrlOverride(raw: String) = viewModelScope.launch {
        val cleaned = raw.trim()
        if (cleaned.isBlank()) baseUrlStore.clear() else baseUrlStore.set(cleaned)
    }
    fun clearBaseUrlOverride() = viewModelScope.launch { baseUrlStore.clear() }

    fun submit() = viewModelScope.launch {
        _state.update { it.copy(submitting = true, formError = null) }
        when (val r = authRepo.login(_state.value.msisdn, _state.value.password)) {
            is ApiResult.Ok -> when (val out = r.value) {
                is AuthRepository.LoginOutcome.Tokens -> _events.value = Event.LoggedIn
                is AuthRepository.LoginOutcome.Otp -> _events.value = Event.GoOtp(out.challenge.challengeToken)
            }
            is ApiResult.Err -> _state.update { it.copy(formError = r.error.userMessage(), submitting = false) }
        }
        _state.update { it.copy(submitting = false) }
    }
}

@Composable
fun LoginScreen(nav: NavHostController, vm: LoginViewModel = hiltViewModel()) {
    val s by vm.state.collectAsState()
    val ev by vm.events.collectAsState()
    val override by vm.baseUrlOverride.collectAsState()
    val gate: AuthGate = hiltViewModel()

    var showPhysical by rememberSaveable { mutableStateOf(false) }
    var ipInput by rememberSaveable { mutableStateOf("") }
    LaunchedEffect(override) { if (override != null) ipInput = override.orEmpty() }

    LaunchedEffect(ev) {
        when (val e = ev) {
            is LoginViewModel.Event.GoOtp -> { nav.navigate(Routes.otp(e.token)); vm.consume() }
            LoginViewModel.Event.LoggedIn -> { gate.markLoggedIn(); nav.navigate(Routes.home) { popUpTo(0) }; vm.consume() }
            null -> Unit
        }
    }
    Column(
        Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text("VulnMNO", style = MaterialTheme.typography.headlineMedium)
        Spacer(Modifier.height(16.dp))
        OutlinedTextField(
            value = s.msisdn, onValueChange = vm::onMsisdn,
            label = { Text("Phone number") },
            keyboardOptions = androidx.compose.foundation.text.KeyboardOptions(keyboardType = KeyboardType.Phone),
            modifier = Modifier.fillMaxWidth(),
        )
        Spacer(Modifier.height(8.dp))
        OutlinedTextField(
            value = s.password, onValueChange = vm::onPassword,
            label = { Text("Password") },
            visualTransformation = PasswordVisualTransformation(),
            modifier = Modifier.fillMaxWidth(),
        )
        Spacer(Modifier.height(16.dp))
        Button(onClick = { vm.submit() }, enabled = !s.submitting, modifier = Modifier.fillMaxWidth()) {
            Text(if (s.submitting) "Signing in…" else "Sign in")
        }
        s.formError?.let { Spacer(Modifier.height(8.dp)); Text(it, color = MaterialTheme.colorScheme.error) }
        Spacer(Modifier.height(8.dp))
        TextButton(onClick = { nav.navigate(Routes.pwResetRequest) }) { Text("Forgot password?") }

        Spacer(Modifier.height(24.dp))
        HorizontalDivider()
        Spacer(Modifier.height(8.dp))

        when {
            // Toggle expanded — collect the IP. Wins over the "override active"
            // branch so the user can edit a previously-set override (Change
            // button below puts us here with `ipInput` pre-filled by the
            // LaunchedEffect above).
            showPhysical -> {
                OutlinedTextField(
                    value = ipInput, onValueChange = { ipInput = it },
                    label = { Text("Backend host") },
                    placeholder = { Text("192.168.1.42  (https/443 via Caddy)") },
                    singleLine = true,
                    keyboardOptions = androidx.compose.foundation.text.KeyboardOptions(keyboardType = KeyboardType.Uri),
                    modifier = Modifier.fillMaxWidth(),
                )
                Spacer(Modifier.height(8.dp))
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(
                        onClick = { vm.setBaseUrlOverride(ipInput); showPhysical = false },
                        enabled = ipInput.isNotBlank(),
                        modifier = Modifier.weight(1f),
                    ) { Text("Use this backend") }
                    OutlinedButton(
                        onClick = {
                            showPhysical = false
                            // Restore the field to the active override (if any)
                            // so a future Change starts from the right value.
                            ipInput = override.orEmpty()
                        },
                        modifier = Modifier.weight(1f),
                    ) { Text("Cancel") }
                }
            }
            // Override is active — show what we're hitting + how to edit / clear it.
            override != null -> {
                Text(
                    "Backend: $override",
                    style = MaterialTheme.typography.labelMedium,
                    fontFamily = FontFamily.Monospace,
                )
                Spacer(Modifier.height(4.dp))
                Row {
                    TextButton(onClick = { ipInput = override.orEmpty(); showPhysical = true }) { Text("Change") }
                    TextButton(onClick = { vm.clearBaseUrlOverride(); showPhysical = false; ipInput = "" }) {
                        Text("Use default")
                    }
                }
            }
            // No override + toggle hidden — show the affordance.
            else -> {
                TextButton(onClick = { showPhysical = true }) { Text("Physical device?") }
            }
        }
    }
}

// ---------- OTP ----------

data class OtpUiState(val challengeToken: String, val code: String = "", val submitting: Boolean = false, val error: String? = null)

@HiltViewModel
class OtpViewModel @Inject constructor(private val authRepo: AuthRepository) : ViewModel() {
    private val _state = MutableStateFlow(OtpUiState(challengeToken = ""))
    val state: StateFlow<OtpUiState> = _state.asStateFlow()
    private val _ok = MutableStateFlow(false)
    val ok: StateFlow<Boolean> = _ok.asStateFlow()
    fun consume() { _ok.value = false }

    fun init(token: String) { _state.value = OtpUiState(challengeToken = token) }
    fun onCode(v: String) = _state.update { it.copy(code = v.take(6), error = null) }

    fun submit() = viewModelScope.launch {
        _state.update { it.copy(submitting = true, error = null) }
        when (val r = authRepo.verifyOtp(_state.value.challengeToken, _state.value.code)) {
            is ApiResult.Ok -> _ok.value = true
            is ApiResult.Err -> _state.update { it.copy(error = r.error.userMessage(), submitting = false) }
        }
        _state.update { it.copy(submitting = false) }
    }
}

@Composable
fun OtpScreen(nav: NavHostController, challengeToken: String, vm: OtpViewModel = hiltViewModel()) {
    val s by vm.state.collectAsState()
    val ok by vm.ok.collectAsState()
    val gate: AuthGate = hiltViewModel()
    LaunchedEffect(challengeToken) { vm.init(challengeToken) }
    LaunchedEffect(ok) {
        if (ok) { gate.markLoggedIn(); nav.navigate(Routes.home) { popUpTo(0) }; vm.consume() }
    }
    Column(Modifier.fillMaxSize().padding(24.dp), verticalArrangement = Arrangement.Center) {
        Text("Enter the 6-digit code", style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(16.dp))
        OutlinedTextField(
            value = s.code, onValueChange = vm::onCode,
            label = { Text("Code") },
            keyboardOptions = androidx.compose.foundation.text.KeyboardOptions(keyboardType = KeyboardType.NumberPassword),
            modifier = Modifier.fillMaxWidth(),
        )
        Spacer(Modifier.height(16.dp))
        Button(onClick = { vm.submit() }, enabled = !s.submitting && s.code.length == 6, modifier = Modifier.fillMaxWidth()) {
            Text(if (s.submitting) "Verifying…" else "Continue")
        }
        s.error?.let { Spacer(Modifier.height(8.dp)); Text(it, color = MaterialTheme.colorScheme.error) }
    }
}

// ---------- Password reset ----------

@HiltViewModel
class PwResetViewModel @Inject constructor(private val authRepo: AuthRepository) : ViewModel() {
    fun request(msisdn: String, onDone: () -> Unit) = viewModelScope.launch { authRepo.requestPasswordReset(msisdn); onDone() }
    fun confirm(msisdn: String, code: String, password: String, onDone: (ok: Boolean) -> Unit) = viewModelScope.launch {
        onDone(authRepo.confirmPasswordReset(msisdn, code, password) is ApiResult.Ok)
    }
}

@Composable
fun PasswordResetRequestScreen(nav: NavHostController, vm: PwResetViewModel = hiltViewModel()) {
    var msisdn by rememberSaveable { mutableStateOf("") }
    var submitting by remember { mutableStateOf(false) }
    Column(Modifier.fillMaxSize().padding(24.dp), verticalArrangement = Arrangement.Center) {
        Text("Reset password", style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(16.dp))
        OutlinedTextField(value = msisdn, onValueChange = { msisdn = it }, label = { Text("Phone number") }, modifier = Modifier.fillMaxWidth())
        Spacer(Modifier.height(16.dp))
        Button(onClick = {
            submitting = true
            vm.request(msisdn) { nav.navigate(Routes.pwResetConfirm(msisdn)) }
        }, enabled = !submitting && msisdn.isNotBlank(), modifier = Modifier.fillMaxWidth()) {
            Text("Send code")
        }
    }
}

@Composable
fun PasswordResetConfirmScreen(nav: NavHostController, msisdn: String, vm: PwResetViewModel = hiltViewModel()) {
    var code by rememberSaveable { mutableStateOf("") }
    var password by rememberSaveable { mutableStateOf("") }
    var error by remember { mutableStateOf<String?>(null) }
    Column(Modifier.fillMaxSize().padding(24.dp), verticalArrangement = Arrangement.Center) {
        Text("Confirm new password", style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(16.dp))
        OutlinedTextField(value = code, onValueChange = { code = it.take(6) }, label = { Text("Code") }, modifier = Modifier.fillMaxWidth())
        Spacer(Modifier.height(8.dp))
        OutlinedTextField(value = password, onValueChange = { password = it }, label = { Text("New password") }, visualTransformation = PasswordVisualTransformation(), modifier = Modifier.fillMaxWidth())
        Spacer(Modifier.height(16.dp))
        Button(onClick = {
            vm.confirm(msisdn, code, password) { ok ->
                if (ok) nav.navigate(Routes.login) { popUpTo(0) }
                else error = "Code invalid or expired"
            }
        }, modifier = Modifier.fillMaxWidth()) { Text("Confirm") }
        error?.let { Spacer(Modifier.height(8.dp)); Text(it, color = MaterialTheme.colorScheme.error) }
    }
}
