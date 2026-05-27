// Hilt and KSP gradle plugins are loaded via the classic buildscript classpath instead of
// the `plugins {}` DSL. Reason: the plugin-marker lookup that `plugins {}` performs is
// fragile against negative Gradle metadata caches and against networks where Maven Central
// path resolution misbehaves for non-Kotlin/non-Android publishers. `buildscript` downloads
// the actual gradle-plugin jar directly. Versions here must stay in sync with the matching
// `[versions]` entries in gradle/libs.versions.toml — the `libs` catalog accessor is not
// available inside `buildscript {}` blocks.
buildscript {
    repositories {
        google()
        // Sonatype's GCS mirror of Maven Central — sidesteps the 429 rate limit on repo1.maven.org.
        maven { url = uri("https://maven-central.storage-download.googleapis.com/maven2/") }
        mavenCentral()
    }
    dependencies {
        classpath("com.google.dagger:hilt-android-gradle-plugin:2.56.2")
        classpath("com.google.devtools.ksp:symbol-processing-gradle-plugin:2.0.20-1.0.25")
    }
}

plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.kotlin.android) apply false
    alias(libs.plugins.kotlin.serialization) apply false
    alias(libs.plugins.kotlin.compose) apply false
}
