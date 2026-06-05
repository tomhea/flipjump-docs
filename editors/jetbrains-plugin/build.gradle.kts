import org.jetbrains.intellij.platform.gradle.TestFrameworkType

plugins {
    id("java")
    id("org.jetbrains.intellij.platform") version "2.1.0"
}

group = "app.tomhe.flipjump"
version = "0.1.0"

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
        // Required by the 2.x instrumentCode task (bytecode @NotNull/form
        // instrumentation); not pulled in transitively at this plugin version.
        instrumentationTools()
    }
    testImplementation("junit:junit:4.13.2")
}

intellijPlatform {
    pluginConfiguration {
        ideaVersion {
            sinceBuild = "232"
            // Unbounded upper bound so the plugin installs on newer IDEs too
            // (the default would pin it to the 2024.2 branch).
            untilBuild = provider { null }
        }
    }
}

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

tasks {
    buildSearchableOptions { enabled = false }
    test { useJUnit() }
}
