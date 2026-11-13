import 'standing.dart';

abstract interface class EsportsRepository {
  /// Regular-season standings for `league` (id | ph | my | kh).
  Future<List<EsportsStanding>> standings(String league);
}
