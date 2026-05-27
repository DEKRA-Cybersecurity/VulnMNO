// Maven Central rate-limits some IP ranges aggressively (HTTP 429). Sonatype maintains
// a high-availability mirror on Google Cloud Storage that is not rate-limited the same way.
// We declare it BEFORE mavenCentral() so Gradle hits the mirror first and only falls back
// to repo1.maven.org if the mirror is unavailable. The URL is duplicated below because
// `pluginManagement {}` and `dependencyResolutionManagement {}` blocks run in isolated
// scopes — top-level vals in settings.gradle.kts are not visible inside them.
pluginManagement {
    repositories {
        google()
        maven {
            url = uri("https://maven-central.storage-download.googleapis.com/maven2/")
            name = "MavenCentralGCSMirror"
        }
        mavenCentral()
        gradlePluginPortal()
    }
}
plugins {
    id("org.gradle.toolchains.foojay-resolver-convention") version "0.10.0"
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        maven {
            url = uri("https://maven-central.storage-download.googleapis.com/maven2/")
            name = "MavenCentralGCSMirror"
        }
        mavenCentral()
    }
}
rootProject.name = "VulnMNO"
include(":app")
