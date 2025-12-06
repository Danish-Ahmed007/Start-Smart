import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'dart:math';

// Single-file StartSmart demo app
// - Material 3 theme with Deep Navy primary and Amber secondary
// - MockApiService acts as the Facade (no real network calls)
// - Riverpod providers implement the Observer Pattern (UI watches providers)

// Data models (GridMetric, Business) are included here for the single-file demo.

class GridMetric {
  final int gridId;
  final String category;
  final double gos; // 0.0 - 10.0
  final double confidence; // 0.0 - 1.0
  final DateTime timestamp;

  GridMetric({
    required this.gridId,
    required this.category,
    required this.gos,
    required this.confidence,
    required this.timestamp,
  });
}

class Business {
  final String name;
  final String location;
  final String category;

  Business({required this.name, required this.location, required this.category});
}

class GridDetail {
  final GridMetric metric;
  final List<Business> competitors;
  final Map<String, double> socialSentiment; // e.g., {"positive":0.7, "negative":0.1}

  GridDetail({required this.metric, required this.competitors, required this.socialSentiment});
}

// MockApiService: Facade Pattern implementation for demo (returns fake data)
class MockApiService {
  final Random _rnd = Random(42);

  Future<List<GridMetric>> getRecommendations(String category, String neighborhood) async {
    // Simulate network latency
    await Future.delayed(const Duration(milliseconds: 700));
    // Generate 20 grid metrics with dummy scores
    return List.generate(20, (i) {
      final gos = double.parse(((_rnd.nextDouble() * 10)).toStringAsFixed(2));
      final conf = double.parse((0.5 + _rnd.nextDouble() * 0.5).toStringAsFixed(2));
      return GridMetric(
        gridId: i + 1,
        category: category,
        gos: gos,
        confidence: conf,
        timestamp: DateTime.now().subtract(Duration(hours: _rnd.nextInt(72))),
      );
    });
  }

  Future<GridDetail> getGridDetails(int gridId) async {
    await Future.delayed(const Duration(milliseconds: 400));
    final metric = GridMetric(
      gridId: gridId,
      category: ['Cafe', 'Retail', 'Gym'][_rnd.nextInt(3)],
      gos: double.parse((_rnd.nextDouble() * 10).toStringAsFixed(2)),
      confidence: double.parse((0.5 + _rnd.nextDouble() * 0.5).toStringAsFixed(2)),
      timestamp: DateTime.now().subtract(Duration(hours: _rnd.nextInt(72))),
    );
    final competitors = List.generate(3, (i) => Business(name: 'Competitor ${i + 1}', location: 'Loc ${i + 1}', category: metric.category));
    final social = {
      'positive': double.parse((0.5 + _rnd.nextDouble() * 0.5).toStringAsFixed(2)),
      'neutral': double.parse((_rnd.nextDouble() * 0.3).toStringAsFixed(2)),
      'negative': double.parse((_rnd.nextDouble() * 0.3).toStringAsFixed(2)),
    };
    return GridDetail(metric: metric, competitors: competitors, socialSentiment: social);
  }

  Future<bool> submitFeedback(int gridId, String comment, int rating) async {
    await Future.delayed(const Duration(milliseconds: 300));
    return true;
  }
}

// Riverpod providers — Observer Pattern in use when UI uses ref.watch(...)
final mockApiProvider = Provider<MockApiService>((ref) => MockApiService());
final selectedCategoryProvider = StateProvider<String?>((ref) => null);
final selectedNeighborhoodProvider = StateProvider<String?>((ref) => null);

// recommendationsProvider watches selectedCategory and selectedNeighborhood
final recommendationsProvider = FutureProvider<List<GridMetric>>((ref) async {
  final cat = ref.watch(selectedCategoryProvider).state;
  final neigh = ref.watch(selectedNeighborhoodProvider).state;
  if (cat == null || neigh == null) return <GridMetric>[];
  final api = ref.read(mockApiProvider);
  return api.getRecommendations(cat, neigh);
});

final gridDetailProvider = FutureProvider.family<GridDetail, int>((ref, gridId) async {
  final api = ref.read(mockApiProvider);
  return api.getGridDetails(gridId);
});

// Utility: color for gos value
Color heatColor(double gos) {
  // gos is 0-10 -> normalize 0-1
  final n = (gos / 10).clamp(0.0, 1.0);
  if (n >= 0.7) return Colors.green.shade600;
  if (n >= 0.4) return Colors.amber.shade600;
  return Colors.red.shade600;
}

// Main application entry point
void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    const deepNavy = Color(0xFF06283D);
    const amber = Color(0xFFFFB300);

    final colorScheme = ColorScheme.fromSeed(seedColor: deepNavy).copyWith(secondary: amber, primary: deepNavy);

    return ProviderScope(
      child: MaterialApp(
        debugShowCheckedModeBanner: false,
        title: 'StartSmart Demo',
        theme: ThemeData(
          useMaterial3: true,
          colorScheme: colorScheme,
          scaffoldBackgroundColor: Colors.grey.shade50,
          cardTheme: CardTheme(
            elevation: 6,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
          ),
          elevatedButtonTheme: ElevatedButtonThemeData(
            style: ElevatedButton.styleFrom(
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 28),
            ),
          ),
          textTheme: const TextTheme(
            headlineLarge: TextStyle(fontWeight: FontWeight.bold, fontSize: 28),
            titleLarge: TextStyle(fontWeight: FontWeight.w700, fontSize: 18),
            bodyMedium: TextStyle(fontSize: 15),
          ),
        ),
        home: const LandingScreen(),
      ),
    );
  }
}

// LandingScreen: Welcome card and selectors
class LandingScreen extends ConsumerWidget {
  const LandingScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final categories = ['Cafe', 'Retail', 'Gym', 'Restaurant'];
    final neighborhoods = ['Downtown', 'Uptown', 'Suburb'];

    final selectedCategory = ref.watch(selectedCategoryProvider).state;
    final selectedNeighborhood = ref.watch(selectedNeighborhoodProvider).state;

    return Scaffold(
      appBar: AppBar(title: const Text('StartSmart')),
      body: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Welcome to StartSmart', style: Theme.of(context).textTheme.headlineLarge),
                    const SizedBox(height: 8),
                    Text('Analyze business opportunities in your neighborhood', style: Theme.of(context).textTheme.bodyMedium),
                    const SizedBox(height: 18),
                    Row(
                      children: [
                        Expanded(
                          child: DecoratedBox(
                            decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12)),
                            child: Padding(
                              padding: const EdgeInsets.symmetric(horizontal: 12),
                              child: DropdownButton<String>(
                                isExpanded: true,
                                value: selectedCategory,
                                hint: const Text('Select Category'),
                                underline: const SizedBox.shrink(),
                                items: categories.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
                                onChanged: (v) => ref.read(selectedCategoryProvider).state = v,
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: DecoratedBox(
                            decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12)),
                            child: Padding(
                              padding: const EdgeInsets.symmetric(horizontal: 12),
                              child: DropdownButton<String>(
                                isExpanded: true,
                                value: selectedNeighborhood,
                                hint: const Text('Select Neighborhood'),
                                underline: const SizedBox.shrink(),
                                items: neighborhoods.map((n) => DropdownMenuItem(value: n, child: Text(n))).toList(),
                                onChanged: (v) => ref.read(selectedNeighborhoodProvider).state = v,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),
                    Align(
                      alignment: Alignment.center,
                      child: ElevatedButton.icon(
                        icon: const Icon(Icons.analytics),
                        label: const Padding(
                          padding: EdgeInsets.symmetric(horizontal: 8.0),
                          child: Text('Analyze', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                        ),
                        style: ElevatedButton.styleFrom(shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)), elevation: 8),
                        onPressed: (selectedCategory != null && selectedNeighborhood != null)
                            ? () {
                                // Navigate to Dashboard
                                Navigator.of(context).push(MaterialPageRoute(builder: (_) => const DashboardScreen()));
                              }
                            : null,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 18),
            Expanded(
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: const [
                      Text('How it works', style: TextStyle(fontWeight: FontWeight.bold)),
                      SizedBox(height: 8),
                      Text('Select a category and neighborhood, then press Analyze to see heatmaps and recommendations.'),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// DashboardScreen with BottomNavigation for Map and Recommendations
class DashboardScreen extends ConsumerStatefulWidget {
  const DashboardScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends ConsumerState<DashboardScreen> {
  int _selectedIndex = 0;

  @override
  Widget build(BuildContext context) {
    final pages = [const MapTab(), const RecommendationsTab()];
    return Scaffold(
      appBar: AppBar(title: const Text('Dashboard')),
      body: pages[_selectedIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (i) => setState(() => _selectedIndex = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.map), label: 'Map'),
          NavigationDestination(icon: Icon(Icons.star), label: 'Recs'),
        ],
      ),
    );
  }
}

// MapTab: heatmap grid
class MapTab extends ConsumerWidget {
  const MapTab({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Observer Pattern: watch recommendationsProvider so UI auto-refreshes
    final recs = ref.watch(recommendationsProvider);

    return Padding(
      padding: const EdgeInsets.all(12.0),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(12.0),
          child: recs.when(
            data: (list) {
              if (list.isEmpty) return const Center(child: Text('No data — go back and select options'));
              return GridView.builder(
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: 4, crossAxisSpacing: 8, mainAxisSpacing: 8),
                itemCount: list.length,
                itemBuilder: (c, i) {
                  final g = list[i];
                  return InkWell(
                    borderRadius: BorderRadius.circular(12),
                    onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => GridDetailScreen(gridId: g.gridId))),
                    child: Container(
                      decoration: BoxDecoration(color: heatColor(g.gos), borderRadius: BorderRadius.circular(12)),
                      child: Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text('G${g.gridId}', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                            Text(g.gos.toStringAsFixed(1), style: const TextStyle(color: Colors.white)),
                          ],
                        ),
                      ),
                    ),
                  );
                },
              );
            },
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (e, st) => Center(child: Text('Error: $e')),
          ),
        ),
      ),
    );
  }
}

// RecommendationsTab: top 3 opportunities
class RecommendationsTab extends ConsumerWidget {
  const RecommendationsTab({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final recs = ref.watch(recommendationsProvider);
    return Padding(
      padding: const EdgeInsets.all(12.0),
      child: recs.when(
        data: (list) {
          if (list.isEmpty) return const Center(child: Text('No recommendations yet'));
          final top = List<GridMetric>.from(list)..sort((a, b) => b.gos.compareTo(a.gos));
          final items = top.take(3).toList();
          return ListView.builder(
            itemCount: items.length,
            itemBuilder: (c, i) {
              final g = items[i];
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(12.0),
                  child: Row(
                    children: [
                      CircleAvatar(backgroundColor: heatColor(g.gos), child: Text((i + 1).toString(), style: const TextStyle(color: Colors.white))),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('${g.category} — Grid ${g.gridId}', style: Theme.of(context).textTheme.titleLarge),
                            const SizedBox(height: 6),
                            Text('Score: ${g.gos.toStringAsFixed(1)} • Confidence: ${(g.confidence * 100).toStringAsFixed(0)}%'),
                            const SizedBox(height: 8),
                            Text('Why: Strong foot traffic and low competition', style: const TextStyle(color: Colors.black54)),
                          ],
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.arrow_forward),
                        onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => GridDetailScreen(gridId: g.gridId))),
                      )
                    ],
                  ),
                ),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, st) => Center(child: Text('Error: $e')),
      ),
    );
  }
}

// GridDetailScreen: shows competitors and social sentiment
class GridDetailScreen extends ConsumerWidget {
  final int gridId;
  const GridDetailScreen({Key? key, required this.gridId}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final detail = ref.watch(gridDetailProvider(gridId));
    return Scaffold(
      appBar: AppBar(title: Text('Grid $gridId')),
      body: Padding(
        padding: const EdgeInsets.all(12.0),
        child: detail.when(
          data: (d) {
            return Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('GOS: ${d.metric.gos.toStringAsFixed(2)}', style: Theme.of(context).textTheme.titleLarge),
                    const SizedBox(height: 8),
                    Text('Confidence: ${(d.metric.confidence * 100).toStringAsFixed(0)}%'),
                    const SizedBox(height: 12),
                    const Text('Competitors', style: TextStyle(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    ...d.competitors.map((c) => ListTile(title: Text(c.name), subtitle: Text(c.location))).toList(),
                    const SizedBox(height: 12),
                    const Text('Social Sentiment', style: TextStyle(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    Row(
                      children: d.socialSentiment.entries.map((e) {
                        return Expanded(
                          child: Column(
                            children: [
                              Text(e.key, style: const TextStyle(fontWeight: FontWeight.bold)),
                              const SizedBox(height: 6),
                              LinearProgressIndicator(value: e.value, color: e.key == 'positive' ? Colors.green : (e.key == 'negative' ? Colors.red : Colors.grey), backgroundColor: Colors.grey.shade200),
                              const SizedBox(height: 6),
                              Text('${(e.value * 100).toStringAsFixed(0)}%'),
                            ],
                          ),
                        );
                      }).toList(),
                    ),
                    const SizedBox(height: 18),
                    ElevatedButton(
                      onPressed: () async {
                        await ref.read(mockApiProvider).submitFeedback(gridId, 'Looks promising', 5);
                        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Feedback submitted')));
                      },
                      child: const Text('Submit Feedback'),
                    )
                  ],
                ),
              ),
            );
          },
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, st) => Center(child: Text('Error: $e')),
        ),
      ),
    );
  }
}



void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter Demo',
      theme: ThemeData(
        // This is the theme of your application.
        //
        // TRY THIS: Try running your application with "flutter run". You'll see
        // the application has a purple toolbar. Then, without quitting the app,
        // try changing the seedColor in the colorScheme below to Colors.green
        // and then invoke "hot reload" (save your changes or press the "hot
        // reload" button in a Flutter-supported IDE, or press "r" if you used
        // the command line to start the app).
        //
        // Notice that the counter didn't reset back to zero; the application
        // state is not lost during the reload. To reset the state, use hot
        // restart instead.
        //
        // This works for code too, not just values: Most code changes can be
        // tested with just a hot reload.
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
      ),
      home: const MyHomePage(title: 'Flutter Demo Home Page'),
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({super.key, required this.title});

  // This widget is the home page of your application. It is stateful, meaning
  // that it has a State object (defined below) that contains fields that affect
  // how it looks.

  // This class is the configuration for the state. It holds the values (in this
  // case the title) provided by the parent (in this case the App widget) and
  // used by the build method of the State. Fields in a Widget subclass are
  // always marked "final".

  final String title;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  int _counter = 0;

  void _incrementCounter() {
    setState(() {
      // This call to setState tells the Flutter framework that something has
      // changed in this State, which causes it to rerun the build method below
      // so that the display can reflect the updated values. If we changed
      // _counter without calling setState(), then the build method would not be
      // called again, and so nothing would appear to happen.
      _counter++;
    });
  }

  @override
  Widget build(BuildContext context) {
    // This method is rerun every time setState is called, for instance as done
    // by the _incrementCounter method above.
    //
    // The Flutter framework has been optimized to make rerunning build methods
    // fast, so that you can just rebuild anything that needs updating rather
    // than having to individually change instances of widgets.
    return Scaffold(
      appBar: AppBar(
        // TRY THIS: Try changing the color here to a specific color (to
        // Colors.amber, perhaps?) and trigger a hot reload to see the AppBar
        // change color while the other colors stay the same.
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        // Here we take the value from the MyHomePage object that was created by
        // the App.build method, and use it to set our appbar title.
        title: Text(widget.title),
      ),
      body: Center(
        // Center is a layout widget. It takes a single child and positions it
        // in the middle of the parent.
        child: Column(
          // Column is also a layout widget. It takes a list of children and
          // arranges them vertically. By default, it sizes itself to fit its
          // children horizontally, and tries to be as tall as its parent.
          //
          // Column has various properties to control how it sizes itself and
          // how it positions its children. Here we use mainAxisAlignment to
          // center the children vertically; the main axis here is the vertical
          // axis because Columns are vertical (the cross axis would be
          // horizontal).
          //
          // TRY THIS: Invoke "debug painting" (choose the "Toggle Debug Paint"
          // action in the IDE, or press "p" in the console), to see the
          // wireframe for each widget.
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            const Text('You have pushed the button this many times:'),
            Text(
              '$_counter',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _incrementCounter,
        tooltip: 'Increment',
        child: const Icon(Icons.add),
      ), // This trailing comma makes auto-formatting nicer for build methods.
    );
  }
}
