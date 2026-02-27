import Foundation

// MARK: - Built-in Example Programs

enum ExamplePrograms {
    static let defaultCode = """
    // Welcome to TinyTalk!
    // Press \u{2318}Enter (or click Run) to execute.

    let name = "World"
    show("Hello, {name}!")

    // Step chains — TinyTalk's superpower
    let data = [42, 17, 93, 5, 68, 31, 84]
    let top3 = data _sort _reverse _take(3)
    show("Top 3:" top3)

    // Functions
    fn factorial(n) {
        if n <= 1 { return 1 }
        return n * factorial(n - 1)
    }
    show("10! = {factorial(10)}")

    """

    struct Example: Identifiable {
        let id = UUID()
        let name: String
        let code: String
    }

    static let builtIn: [Example] = [
        Example(name: "Hello World", code: """
        // Hello World - TinyTalk
        // Two styles, one language.

        // === Modern Style ===
        let name = "World"
        show("Hello, {name}!")

        // Variables and arithmetic
        let x = 10
        let y = 20
        show("{x} + {y} = {x + y}")

        // Functions
        fn square(x) {
            return x * x
        }
        show("5 squared is {square(5)}")

        // Step chains - the standout feature
        let numbers = [5, 3, 8, 1, 9, 2, 7, 4, 6]
        show("Sorted top 3:" numbers _sort _reverse _take(3))

        // === Classic Style (Smalltalk-inspired) ===
        when PI = 3.14159

        law circle_area(r)
            reply PI * r * r
        end

        show("Area of circle with r=5:" circle_area(5))
        """),

        Example(name: "Fibonacci", code: """
        // Fibonacci in TinyTalk

        fn fib(n) {
            if n <= 1 { return n }
            return fib(n - 1) + fib(n - 2)
        }

        // First 15 fibonacci numbers
        for i in range(15) {
            show("fib({i}) = {fib(i)}")
        }
        """),

        Example(name: "Step Chains", code: """
        // Step Chains - TinyTalk's signature feature

        let data = [42, 17, 93, 5, 68, 31, 84, 12, 56, 29]

        // Sort and take top 5
        show("Top 5:" data _sort _reverse _take(5))

        // Filter and count
        show("Count > 30:" data _filter((x) => x > 30) _count)

        // Map and sum
        show("Doubled sum:" data _map((x) => x * 2) _sum)

        // Unique values
        let dupes = [1, 2, 2, 3, 3, 3, 4]
        show("Unique:" dupes _unique)

        // Chain multiple operations
        let result = data _filter((x) => x > 20) _sort _map((x) => x * 10) _take(3)
        show("Filtered > 20, sorted, x10, top 3:" result)

        // Group by even/odd
        let nums = [1, 2, 3, 4, 5, 6, 7, 8]
        let grouped = nums _group((x) => x % 2 == 0 ? "even" : "odd")
        show("Grouped:" grouped)

        // Statistics
        show("Min:" data _min)
        show("Max:" data _max)
        show("Sum:" data _sum)
        show("Avg:" data _avg)
        """),

        Example(name: "Data Pipeline", code: """
        // Data Pipeline — clean, transform, analyze

        let sales = [
            {"product": "Widget", "region": "North", "amount": 150},
            {"product": "Gadget", "region": "South", "amount": 300},
            {"product": "Widget", "region": "South", "amount": 200},
            {"product": "Gadget", "region": "North", "amount": 450},
            {"product": "Widget", "region": "North", "amount": 175},
            {"product": "Gadget", "region": "South", "amount": 280},
        ]

        // Total by product
        let by_product = sales
            _groupBy((r) => r["product"])
            _summarize({"total": (rows) => rows _map((r) => r["amount"]) _sum})
        show("Sales by product:" by_product)

        // Top earners
        let top = sales _arrange((r) => r["amount"]) _reverse _take(3)
        show("Top 3 sales:" top)
        """),

        Example(name: "Blueprint (OOP)", code: """
        // Blueprint — TinyTalk's class system

        blueprint Counter
            field value = 0

            forge inc()
                self.value = self.value + 1
                reply self.value
            end

            forge dec()
                self.value = self.value - 1
                reply self.value
            end

            forge reset()
                self.value = 0
                reply self.value
            end
        end

        let c = Counter(0)
        show("Increment:" c.inc() c.inc() c.inc())
        show("Current:" c.value)
        show("Decrement:" c.dec())
        show("Reset:" c.reset())
        """),

        Example(name: "Pattern Matching", code: """
        // Pattern Matching in TinyTalk

        fn describe(x) {
            match x {
                0 => "zero",
                1 => "one",
                2 => "two",
                _ => "many: {x}",
            }
        }

        for i in range(5) {
            show("{i} is {describe(i)}")
        }

        // Match with types
        fn classify(val) {
            match type(val) {
                "int" => "integer: {val}",
                "string" => "text: {val}",
                "list" => "list with {len(val)} items",
                _ => "other: {val}",
            }
        }

        show(classify(42))
        show(classify("hello"))
        show(classify([1, 2, 3]))
        """),
    ]
}
