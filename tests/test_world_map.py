import unittest
from dataset_world_map import archive_groups, resolve_species, valid_coordinate


class WorldCoverageTests(unittest.TestCase):
    def test_shared_records_do_not_become_additive_species_or_location_totals(self):
        rows = [dict(record_number='same', animal={'genus':[{'name':'a'}, {'name':'b'}]},
                     location={'name':['region'], 'coordinates':[{'lat':1,'lon':2}, {'lat':1,'lon':2}, {'lat':3,'lon':4}]}),
                dict(record_number='same', animal={'genus':[{'name':'a'}]},
                     location={'name':['alias'], 'coordinates':[{'lat':1,'lon':2}]}),
                dict(record_number='noise', animal={'genus':[{'name':'noise'}]},
                     location={'name':[], 'coordinates':[{'lat':1,'lon':2}]})]
        groups, ids = archive_groups(rows, lambda name: None if name == 'noise' else (name, 'key','family'))
        self.assertEqual(ids, {'same'})
        self.assertEqual(len(groups), 2)
        self.assertEqual(groups[(2,1)]['taxa']['a'], {'same'})
        self.assertEqual(groups[(2,1)]['taxa']['b'], {'same'})
        self.assertEqual(groups[(2,1)]['names'], {'region','alias'})

    def test_historical_subspecies_collapses_to_species_and_unreviewed_fuzzy_match_fails(self):
        accepted = {'2':{'species':'Delphinus delphis','speciesKey':3,'family':'Delphinidae'}}
        matches = {'Delphinus bairdii': {'usageKey':1,'acceptedUsageKey':2,'matchType':'EXACT'}}
        self.assertEqual(resolve_species('Delphinus bairdii',matches,accepted), ('Delphinus delphis','3','Delphinidae'))
        matches['unreviewed'] = {'usageKey':2,'matchType':'FUZZY'}
        with self.assertRaisesRegex(ValueError,'Unreviewed'):
            resolve_species('unreviewed',matches,accepted)
        self.assertIsNone(resolve_species('Ambient X',matches,accepted))

    def test_coordinate_validation_preserves_eastern_aleutians_and_rejects_nonfinite(self):
        self.assertTrue(valid_coordinate(178.52,52.32))
        self.assertFalse(valid_coordinate(float('nan'),52))
        self.assertFalse(valid_coordinate(-181,52))
        self.assertFalse(valid_coordinate(-120,91))


if __name__ == '__main__':
    unittest.main()
