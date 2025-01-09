"""Label generation functionality for floor plans."""

from nautobot_floor_plan.choices import (
    AxisLabelsChoices,
    CustomAxisLabelsChoices,
)
from nautobot_floor_plan.utils.label_converters import LabelConverterFactory
from nautobot_floor_plan.utils.utils import (
    extract_prefix_and_letter,
    extract_prefix_and_number,
    grid_letter_to_number,
    grid_number_to_letter,
)


class FloorPlanLabelGenerator:
    """Handles generation of labels for floor plan axes."""

    def __init__(self, floor_plan):
        """Store instance of floor plan."""
        self.floor_plan = floor_plan

    def generate_labels(self, axis, count):
        """Generate labels for the specified axis."""
        # Get custom ranges in the order they were created
        custom_ranges = self.floor_plan.custom_labels.filter(axis=axis).order_by("id")

        if not custom_ranges.exists():
            return self._generate_default_labels(axis, count)

        labels = []
        for custom_range in custom_ranges:
            range_labels = self._generate_labels_for_range(
                custom_range,
                custom_range.increment_letter,
            )
            labels.extend(range_labels)

            if len(labels) >= count:
                return labels[:count]

        # If custom ranges don't provide enough labels, fall back to default labeling
        if len(labels) < count:
            remaining_count = count - len(labels)
            if axis == "X":
                start = self.floor_plan.x_origin_seed + (len(labels) * self.floor_plan.x_axis_step)
                step = self.floor_plan.x_axis_step
                is_letters = self.floor_plan.x_axis_labels == AxisLabelsChoices.LETTERS
            else:
                start = self.floor_plan.y_origin_seed + (len(labels) * self.floor_plan.y_axis_step)
                step = self.floor_plan.y_axis_step
                is_letters = self.floor_plan.y_axis_labels == AxisLabelsChoices.LETTERS

            default_labels = self._generate_default_range(start, step, remaining_count, is_letters)
            labels.extend(default_labels)

        return labels

    def _generate_default_labels(self, axis, count):
        """Generate default labels for an axis."""
        if axis == "X":
            start = self.floor_plan.x_origin_seed
            step = self.floor_plan.x_axis_step
            is_letters = self.floor_plan.x_axis_labels == AxisLabelsChoices.LETTERS
        else:
            start = self.floor_plan.y_origin_seed
            step = self.floor_plan.y_axis_step
            is_letters = self.floor_plan.y_axis_labels == AxisLabelsChoices.LETTERS

        return self._generate_default_range(start, step, count, is_letters)

    def _generate_default_range(self, start, step, count, is_letters):
        """Generate a sequence of default labels."""
        labels = []
        current = start

        for _ in range(count):
            if is_letters:
                # Wrap around to 18278 (ZZZ) when going in reverse
                if current < 1:
                    current = 18278 + current
                elif current > 18278:
                    current = current - 18278
                labels.append(grid_number_to_letter(current))
            else:
                labels.append(str(current))
            current += step

        return labels

    def _generate_labels_for_range(self, custom_range, increment_letter=True):
        """Helper to generate labels for a given range."""
        labels = []
        start = str(custom_range.start_label)
        end = str(custom_range.end_label)
        step = custom_range.step
        label_type = custom_range.label_type

        try:
            converter = LabelConverterFactory.get_converter(label_type)

            if label_type == CustomAxisLabelsChoices.NUMBERS:
                converter.set_number_only_mode(True)
            elif label_type == CustomAxisLabelsChoices.ALPHANUMERIC:
                converter.set_increment_prefix(increment_letter)

            if label_type in [CustomAxisLabelsChoices.NUMALPHA, CustomAxisLabelsChoices.LETTERS]:
                if label_type == CustomAxisLabelsChoices.LETTERS:
                    labels = self._generate_letter_labels(start, end, increment_letter, step)
                else:
                    labels = self._generate_numalpha_labels(start, end, increment_letter, step)
            else:
                labels = self._generate_numeric_labels(converter, start, end, step)

        except ValueError as e:
            raise ValueError(f"Error in label generation: {e}") from e

        return labels

    def _generate_numalpha_labels(self, start, end, increment_letter, step=1):
        """Generate labels for NUMALPHA type."""
        labels = []
        start_prefix, start_letters = extract_prefix_and_letter(start)
        end_prefix, end_letters = extract_prefix_and_letter(end)

        if start_prefix != end_prefix:
            raise ValueError(f"Prefix mismatch: {start_prefix} != {end_prefix}")

        current_prefix, current_letters = start_prefix, start_letters

        while True:
            labels.append(f"{current_prefix}{current_letters}")

            if labels[-1] == end:
                break

            if step > 0:
                current_letters = self._increment_letters(current_letters, increment_letter, len(current_letters))
                if self._should_stop_label_generation(current_letters, end_letters):
                    break
            else:
                current_letters = self._decrement_letters(current_letters, increment_letter, end_letters)
                if not current_letters:
                    break

        return labels

    def _generate_letter_labels(self, start, end, increment_letter, step=1):
        """Generate labels for LETTERS type."""
        labels = []
        start_prefix, start_letters = extract_prefix_and_number(start)
        _, end_letters = extract_prefix_and_number(end)

        while True:
            labels.append(f"{start_prefix}{start_letters}")

            if start_letters == end_letters:
                break

            # Increment or decrement letters based on step direction
            if step > 0:
                start_letters = self._increment_letters(start_letters, increment_letter, len(start_letters))
            else:
                start_letters = self._decrement_letters(start_letters, increment_letter, end_letters)

        return labels

    def _increment_letters(self, current_letters, increment_letter, length):
        """Increment the letters based on the desired strategy."""
        if increment_letter:
            # Use grid_number_to_letter and grid_letter_to_number for the carry-over logic
            current_number = grid_letter_to_number(current_letters)
            next_number = current_number + 1
            return grid_number_to_letter(next_number)
        # Increment all letters
        next_letter = chr(ord(current_letters[0]) + 1)
        return next_letter * length

    def _decrement_letters(self, letters, increment_letter, end_letters):
        """Decrement letters in a label."""
        if not letters:
            return None

        # Convert letters to list for manipulation
        letter_list = list(letters)

        if increment_letter:
            # Only decrement the last letter
            last_idx = len(letter_list) - 1
            if letter_list[last_idx] > "A":
                letter_list[last_idx] = chr(ord(letter_list[last_idx]) - 1)
            else:
                return None
        else:
            # Decrement all letters together
            for i, letter in enumerate(letter_list):
                if letter > "A":
                    letter_list[i] = chr(ord(letter) - 1)
                else:
                    return None

        result = "".join(letter_list)

        # Check if we've gone past the end
        if end_letters and (
            (increment_letter and result < end_letters) or (not increment_letter and result < end_letters)
        ):
            return None

        return result

    def _generate_numeric_labels(self, converter, start, end, step):
        """Generate labels for numeric or other types."""
        labels = []
        # Set the format based on the start label
        if hasattr(converter, "set_format"):
            converter.set_format(start)

        current = converter.to_numeric(start)
        end_val = converter.to_numeric(end)

        while True:
            labels.append(converter.from_numeric(current))
            if current == end_val:
                break
            current += step
            if (step > 0 and current > end_val) or (step < 0 and current < end_val):
                break
        return labels

    def _should_stop_label_generation(self, current_letters, end_letters):
        """Determine if the label generation should stop."""
        if len(current_letters) > len(end_letters):
            return True
        if len(current_letters) == len(end_letters) and current_letters > end_letters:
            return True
        return False
