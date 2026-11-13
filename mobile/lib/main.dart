import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_web_plugins/url_strategy.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'app.dart';
import 'shared/local/local_store.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Hash URLs let the app be hosted statically (no SPA rewrite rules needed):
  // /#/heroes, /#/hero/88, /#/esports …
  setUrlStrategy(const HashUrlStrategy());

  // Load lightweight on-device preferences and expose them through Riverpod.
  final prefs = await SharedPreferences.getInstance();

  runApp(
    ProviderScope(
      overrides: [
        localStoreProvider.overrideWithValue(LocalStore(prefs)),
      ],
      child: const MlbbApp(),
    ),
  );
}
