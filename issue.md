# Non-existent value in tag filter returns all objects

Following test returns all objects:

```python
class TestFloorPlanFilterSet(TestCase):

    ...

    def test_tag(self):
        """Test filtering by Tag."""
        self.floors[0].floor_plan.tags.add(Tag.objects.create(name="Planned"))
        params = {"tag": ["planned"]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
```

When fixing this, filter works as expected:

```python
...
        params = {"tag": ["Planned"]}
...
```
