#!/usr/bin/env swift
/**
 * SwiftUI → PNG モックアップレンダラー
 *
 * 使用方法:
 *   swift render-mockup-swift.swift <swift-file> <output-png> [device]
 *   swift render-mockup-swift.swift LoginView.swift mockups/login.png "iPhone 15 Pro"
 *
 * 必要条件:
 *   - macOS 13.0+
 *   - Xcode 15.0+ (Command Line Tools)
 */

import Foundation

// デバイスプリセット
let devices: [String: (width: Int, height: Int, scale: Int)] = [
    "iPhone SE": (375, 667, 2),
    "iPhone 15": (393, 852, 3),
    "iPhone 15 Pro": (393, 852, 3),
    "iPhone 15 Pro Max": (430, 932, 3),
    "iPad Pro 11": (834, 1194, 2),
    "iPad Pro 12.9": (1024, 1366, 2),
]

func printUsage() {
    print("""
    📱 SwiftUI モックアップレンダラー

    使用方法:
      swift render-mockup-swift.swift <swift-file> <output-png> [device]

    デバイスプリセット:
      iPhone SE        : 375x667
      iPhone 15        : 393x852
      iPhone 15 Pro    : 393x852 (デフォルト)
      iPhone 15 Pro Max: 430x932
      iPad Pro 11      : 834x1194
      iPad Pro 12.9    : 1024x1366

    例:
      swift render-mockup-swift.swift LoginView.swift mockups/login.png
      swift render-mockup-swift.swift Dashboard.swift mockups/dashboard.png "iPad Pro 11"
    """)
}

func main() {
    let args = CommandLine.arguments

    guard args.count >= 3 else {
        printUsage()
        exit(1)
    }

    let swiftFile = args[1]
    let outputPath = args[2]
    let deviceName = args.count > 3 ? args[3] : "iPhone 15 Pro"

    guard let device = devices[deviceName] else {
        print("❌ 不明なデバイス: \(deviceName)")
        print("利用可能: \(devices.keys.sorted().joined(separator: ", "))")
        exit(1)
    }

    print("📱 SwiftUI モックアップ生成")
    print("   ファイル: \(swiftFile)")
    print("   デバイス: \(deviceName) (\(device.width)x\(device.height))")
    print("")

    // SwiftUIファイルを読み込んでコンパイル・レンダリング
    // 実際の実装では、swift build + ImageRenderer を使用

    let wrapperCode = generateWrapper(
        swiftFile: swiftFile,
        outputPath: outputPath,
        width: device.width,
        height: device.height,
        scale: device.scale
    )

    // 一時ファイルに書き出し
    let tempDir = FileManager.default.temporaryDirectory
    let wrapperPath = tempDir.appendingPathComponent("MockupRenderer.swift")
    let packagePath = tempDir.appendingPathComponent("Package.swift")

    do {
        try wrapperCode.write(to: wrapperPath, atomically: true, encoding: .utf8)
        try generatePackageSwift().write(to: packagePath, atomically: true, encoding: .utf8)

        // 元のSwiftファイルをコピー
        let sourcePath = tempDir.appendingPathComponent("ContentView.swift")
        try FileManager.default.copyItem(
            at: URL(fileURLWithPath: swiftFile),
            to: sourcePath
        )

        print("[1/3] SwiftUIコード準備中...")
        print("[2/3] コンパイル中...")

        // Swift Build & Run
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/swift")
        process.arguments = ["run", "--package-path", tempDir.path]
        process.currentDirectoryURL = tempDir

        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe

        try process.run()
        process.waitUntilExit()

        if process.terminationStatus == 0 {
            print("[3/3] PNG保存中...")
            print("")
            print("✅ \(outputPath) を作成しました (\(device.width)x\(device.height))")
        } else {
            let output = String(data: pipe.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
            print("❌ レンダリング失敗:")
            print(output)
            exit(1)
        }

    } catch {
        print("❌ エラー: \(error.localizedDescription)")
        exit(1)
    }
}

func generateWrapper(swiftFile: String, outputPath: String, width: Int, height: Int, scale: Int) -> String {
    return """
    import SwiftUI
    import AppKit

    // Include the user's SwiftUI view
    // This would be injected from the source file

    @main
    struct MockupRenderer {
        static func main() {
            // Create the view
            let view = ContentView()
                .frame(width: \(width), height: \(height))
                .background(Color(NSColor.windowBackgroundColor))

            // Render to image
            let renderer = ImageRenderer(content: view)
            renderer.scale = \(scale)

            if let nsImage = renderer.nsImage {
                // Save as PNG
                guard let tiffData = nsImage.tiffRepresentation,
                      let bitmapRep = NSBitmapImageRep(data: tiffData),
                      let pngData = bitmapRep.representation(using: .png, properties: [:])
                else {
                    print("❌ PNG変換失敗")
                    return
                }

                let outputURL = URL(fileURLWithPath: "\(outputPath)")

                // Create directory if needed
                try? FileManager.default.createDirectory(
                    at: outputURL.deletingLastPathComponent(),
                    withIntermediateDirectories: true
                )

                do {
                    try pngData.write(to: outputURL)
                } catch {
                    print("❌ ファイル保存失敗: \\(error)")
                }
            }
        }
    }
    """
}

func generatePackageSwift() -> String {
    return """
    // swift-tools-version:5.9
    import PackageDescription

    let package = Package(
        name: "MockupRenderer",
        platforms: [.macOS(.v13)],
        targets: [
            .executableTarget(
                name: "MockupRenderer",
                path: "."
            )
        ]
    )
    """
}

main()
