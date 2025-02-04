"""Selenium tests for nautobot_floor_plan."""

import unittest

from django.urls import reverse
from nautobot.core.testing.integration import SeleniumTestCase
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait

from nautobot_floor_plan.tests.utils import is_nautobot_version_less_than


@unittest.skipIf(is_nautobot_version_less_than("2.3.1"), "Nautobot version is less than 2.3.1")
class RangeTileTestCase(SeleniumTestCase):
    """Validations against floor plan custom label workflows."""

    def setUp(self):
        """Login and navigate to the floor plan custom label section."""
        super().setUp()

        self.user.is_superuser = True
        self.user.save()
        self.login(self.user.username, self.password)

        self.browser.visit(f"{self.live_server_url}{reverse('plugins:nautobot_floor_plan:floorplan_add')}")
        WebDriverWait(self.browser, 10).until(lambda driver: driver.is_text_present("Add a new floor plan"))

        custom_label_tab = self.browser.find_by_xpath("//a[contains(text(),'Custom Labels')]")[0]
        custom_label_tab.scroll_to()
        custom_label_tab.click()

    def test_custom_label_preview(self):
        """Ensure generate preview and add range is working as intended."""
        # Populate letter range
        self.browser.find_by_css("input#id_x_ranges-0-start").first.value = "A"
        self.browser.find_by_css("input#id_x_ranges-0-end").first.value = "H"

        select_element = self.browser.driver.find_element(By.CSS_SELECTOR, "select#id_x_ranges-0-label_type")
        select = Select(select_element)
        select.select_by_value("letters")

        # Click preview button
        self.browser.find_by_css("button#generate-x-preview").first.click()

        # Get preview content and validate
        self.assertEqual(self.browser.find_by_css("div#x-preview").first.text, "Labels: A, B, C, D, E, F, G, H")

        # Add a second range
        self.browser.find_by_css("button#add-x-range").first.click()
        self.browser.find_by_css("input#id_x_ranges-1-start").first.value = "1"
        self.browser.find_by_css("input#id_x_ranges-1-end").first.value = "8"

        # Check preview again, this time for new range
        self.browser.find_by_css("button#generate-x-preview").first.click()
        self.assertEqual(self.browser.find_by_css("div#x-preview div")[1].text, "Labels: 1, 2, 3, 4, 5, 6, 7, 8")

    def test_custom_label_examples_modal(self):
        """Confirm modal pop-over with examples is working"""
        # Check modal is empty before click
        self.assertEqual(self.browser.find_by_css("div.modal-header h5").first.text, "")

        # Click examples button
        self.browser.find_by_css("button[data-target='#exampleModal']").first.click()

        # Check modal is populated
        WebDriverWait(self.browser, 10).until(lambda driver: driver.is_text_present("Custom Label Ranges Examples"))
        self.assertEqual(self.browser.find_by_css("div.modal-header h5").first.text, "Custom Label Ranges Examples")
