import SwiftUI
#if os(macOS)
import AppKit
#endif

/// ログイン画面のモックアップ
/// AI臭くない、Human Interface Guidelines準拠のデザイン
struct ContentView: View {
    @State private var email = ""
    @State private var password = ""
    @State private var isSecure = true

    var body: some View {
        VStack(spacing: 0) {
            Spacer()

            // Logo
            VStack(spacing: 16) {
                ZStack {
                    RoundedRectangle(cornerRadius: 20)
                        .fill(.indigo.gradient)
                        .frame(width: 72, height: 72)

                    Image(systemName: "bolt.fill")
                        .font(.system(size: 32, weight: .medium))
                        .foregroundStyle(.white)
                }
                .shadow(color: .indigo.opacity(0.3), radius: 16, y: 8)

                VStack(spacing: 4) {
                    Text("おかえりなさい")
                        .font(.title.bold())

                    Text("アカウントにログインしてください")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
            }
            .padding(.bottom, 48)

            // Form
            VStack(spacing: 16) {
                // Email Field
                VStack(alignment: .leading, spacing: 8) {
                    Text("メールアドレス")
                        .font(.subheadline.weight(.medium))
                        .foregroundStyle(.secondary)

                    HStack {
                        TextField("email@example.com", text: $email)
                            .textContentType(.emailAddress)
                            #if os(iOS)
                            .keyboardType(.emailAddress)
                            .autocapitalization(.none)
                            #endif

                        if !email.isEmpty {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundStyle(.green)
                        }
                    }
                    .padding(.horizontal, 16)
                    .padding(.vertical, 14)
                    .background(.gray.opacity(0.08))
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                }

                // Password Field
                VStack(alignment: .leading, spacing: 8) {
                    Text("パスワード")
                        .font(.subheadline.weight(.medium))
                        .foregroundStyle(.secondary)

                    HStack {
                        if isSecure {
                            SecureField("••••••••", text: $password)
                                .textContentType(.password)
                        } else {
                            TextField("••••••••", text: $password)
                        }

                        Button {
                            isSecure.toggle()
                        } label: {
                            Image(systemName: isSecure ? "eye" : "eye.slash")
                                .foregroundStyle(.secondary)
                        }
                    }
                    .padding(.horizontal, 16)
                    .padding(.vertical, 14)
                    .background(.gray.opacity(0.08))
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                }

                // Forgot Password
                HStack {
                    Spacer()
                    Button("パスワードをお忘れですか？") { }
                        .font(.subheadline.weight(.medium))
                        .foregroundStyle(.indigo)
                }
            }
            .padding(.horizontal, 24)

            // Login Button
            Button {
                // Login action
            } label: {
                Text("ログイン")
                    .font(.headline)
                    .foregroundStyle(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 16)
                    .background(.indigo.gradient)
                    .clipShape(RoundedRectangle(cornerRadius: 14))
            }
            .padding(.horizontal, 24)
            .padding(.top, 32)

            // Divider
            HStack {
                Rectangle()
                    .fill(.gray.opacity(0.2))
                    .frame(height: 1)

                Text("または")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                    .padding(.horizontal, 16)

                Rectangle()
                    .fill(.gray.opacity(0.2))
                    .frame(height: 1)
            }
            .padding(.horizontal, 24)
            .padding(.vertical, 24)

            // Social Login
            HStack(spacing: 12) {
                SocialLoginButton(
                    icon: "apple.logo",
                    label: "Apple"
                )

                SocialLoginButton(
                    icon: "g.circle.fill",
                    label: "Google"
                )
            }
            .padding(.horizontal, 24)

            Spacer()

            // Sign Up Link
            HStack(spacing: 4) {
                Text("アカウントをお持ちでないですか？")
                    .foregroundStyle(.secondary)

                Button("新規登録") { }
                    .fontWeight(.semibold)
                    .foregroundStyle(.indigo)
            }
            .font(.subheadline)
            .padding(.bottom, 32)
        }
        #if os(iOS)
        .background(Color(.systemBackground))
        #else
        .background(Color(NSColor.windowBackgroundColor))
        #endif
    }
}

struct SocialLoginButton: View {
    let icon: String
    let label: String

    var body: some View {
        Button {
            // Social login action
        } label: {
            HStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.system(size: 16, weight: .medium))

                Text(label)
                    .font(.subheadline.weight(.medium))
            }
            .foregroundStyle(.primary)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 14)
            .background(.gray.opacity(0.08))
            .clipShape(RoundedRectangle(cornerRadius: 12))
        }
    }
}

// MARK: - Preview

#Preview("Light Mode") {
    ContentView()
}

#Preview("Dark Mode") {
    ContentView()
        .preferredColorScheme(.dark)
}

#Preview("Compact") {
    ContentView()
        .frame(width: 375, height: 667)
}
