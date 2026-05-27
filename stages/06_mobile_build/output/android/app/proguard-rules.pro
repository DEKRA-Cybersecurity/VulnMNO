# Keep Retrofit + Kotlinx Serialization metadata
-keepattributes Signature, *Annotation*, EnclosingMethod, InnerClasses
-keepclassmembers,allowshrinking,allowobfuscation interface * { @retrofit2.http.* <methods>; }
-keep,includedescriptorclasses class kotlinx.serialization.** { *; }
-keepclassmembers class com.vulnmno.app.data.remote.dto.** { *; }
