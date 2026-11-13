import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/dio_client.dart';
import '../data/esports_repository_impl.dart';
import '../domain/esports_repository.dart';
import '../domain/standing.dart';

final esportsRepositoryProvider = Provider<EsportsRepository>(
  (ref) => EsportsRepositoryImpl(ref.watch(dioProvider)),
);

/// Selected league: id | ph | my | kh.
final esportsLeagueProvider = StateProvider<String>((ref) => 'id');

final esportsStandingsProvider =
    FutureProvider.autoDispose<List<EsportsStanding>>((ref) {
  final league = ref.watch(esportsLeagueProvider);
  return ref.watch(esportsRepositoryProvider).standings(league);
});
