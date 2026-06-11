import org.jetbrains.changelog.Changelog
import org.jetbrains.intellij.platform.gradle.TestFrameworkType

plugins {
    id("java")
    id("org.jetbrains.intellij.platform") version "2.16.0"
    // Parses CHANGELOG.md (Keep a Changelog format) so the plugin's
    // "What's new" is generated from the same file VS Code renders as its
    // Changelog tab — single source of truth, no duplicated HTML.
    id("org.jetbrains.changelog") version "2.5.0"
}

group = "app.tomhe.flipjump"
version = "0.2.0"

repositories {
    mavenCentral()
    intellijPlatform {
        defaultRepositories()
        intellijDependencies()
    }
}

dependencies {
    intellijPlatform {
        // IntelliJ IDEA Community as the build base. The plugin depends only on
        // com.intellij.modules.platform, so it loads in every JetBrains IDE
        // (PyCharm, CLion, WebStorm, ...).
        intellijIdeaCommunity("2024.2")
        testFramework(TestFrameworkType.Platform)
    }
    testImplementation("junit:junit:4.13.2")
}

intellijPlatform {
    pluginConfiguration {
        // "What's new" for this version, rendered to HTML from CHANGELOG.md.
        changeNotes = provider {
            changelog.renderItem(changelog.getLatest(), Changelog.OutputType.HTML)
        }
        ideaVersion {
            sinceBuild = "232"
            // Unbounded upper bound so the plugin installs on newer IDEs too
            // (the default would pin it to the 2024.2 branch).
            untilBuild = provider { null }
        }
    }
}

changelog {
    version = project.version.toString()
    // Don't require a [Unreleased] section; we render the latest released entry.
    unreleasedTerm = "Unreleased"
}

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

tasks {
    buildSearchableOptions { enabled = false }
    test { useJUnit() }
}
