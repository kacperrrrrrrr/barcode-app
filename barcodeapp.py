from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window
import random
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.graphics import renderPDF
import os
import barcode
from barcode.writer import ImageWriter
from reportlab.graphics.barcode import code128

Window.size = (400, 700)


def create_bottom_nav(screen):
    nav = BoxLayout(size_hint=(1, 0.1), spacing=10)
    nav.add_widget(Button(text='Home', on_press=lambda x: setattr(screen.manager, 'current', 'home')))
    nav.add_widget(Button(text='Statistics', on_press=lambda x: setattr(screen.manager, 'current', 'stats')))
    nav.add_widget(Button(text='Main Page', on_press=lambda x: setattr(screen.manager, 'current', 'load')))
    return nav


class HomeScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        layout.add_widget(Label(text='Barcode Manager', font_size=32))
        layout.add_widget(Button(text='Start New Session', size_hint=(1, 0.2),
                                 on_press=lambda x: setattr(self.manager, 'current', 'start')))
        layout.add_widget(Button(text='Load Session', size_hint=(1, 0.2),
                                 on_press=lambda x: setattr(self.manager, 'current', 'load')))
        layout.add_widget(create_bottom_nav(self))
        self.add_widget(layout)


class StartSessionScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.layout.add_widget(Label(text='How many barcodes to generate?'))
        self.amount_input = TextInput(multiline=False, input_filter='int')
        self.layout.add_widget(self.amount_input)

        self.feedback = Label(text='')
        self.layout.add_widget(self.feedback)

        generate_btn = Button(text='Generate Barcodes')
        generate_btn.bind(on_press=self.generate_barcodes)
        self.layout.add_widget(generate_btn)

        download_btn = Button(text='Download Barcodes as PDF')
        download_btn.bind(on_press=self.download_barcodes)
        self.layout.add_widget(download_btn)

        self.layout.add_widget(create_bottom_nav(self))
        self.add_widget(self.layout)

    def generate_barcodes(self, instance):
        count = int(self.amount_input.text or 0)
        self.manager.generated_barcodes = [
            str(random.randint(100000000000, 999999999999)) for _ in range(count)
        ]
        self.manager.scanned_barcodes = set()
        self.feedback.text = f"Generated {count} barcodes"

    def download_barcodes(self, instance):
        barcodes = self.manager.generated_barcodes
        if not barcodes:
            self.feedback.text = "No barcodes to download"
            return

        c = canvas.Canvas("barcodes.pdf", pagesize=A4)
        width, height = A4
        barcodes_per_page = 16
        cols = 4
        rows = 4
        margin_x = 15 * mm
        margin_y = 15 * mm
        spacing_x = (width - 2 * margin_x) / cols
        spacing_y = (height - 2 * margin_y) / rows

        for i, code in enumerate(barcodes):
            pos = i % barcodes_per_page
            col = pos % cols
            row = pos // cols

            if pos == 0 and i != 0:
                c.showPage()

            x = margin_x + col * spacing_x
            y = height - margin_y - row * spacing_y

            # Create barcode using python-barcode
            barcode_img = barcode.get_barcode_class('code128')(code, writer=ImageWriter())
            barcode_img.save(f'barcode_{code}')  # Save as PNG file

            # Draw the barcode image in the PDF
            c.drawImage(f'barcode_{code}.png', x, y, width=spacing_x, height=spacing_y)
            os.remove(f'barcode_{code}.png')  # Clean up the temporary barcode image

        c.save()
        self.feedback.text = "PDF saved as barcodes.pdf"
        os.system("open barcodes.pdf")  # Opens the PDF on Mac


class LoadSessionScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        self.scan_input = TextInput(hint_text='Scan Barcode', multiline=False)
        layout.add_widget(self.scan_input)

        scan_btn = Button(text='Scan')
        scan_btn.bind(on_press=self.check_barcode)
        layout.add_widget(scan_btn)

        self.feedback_label = Label(text='')
        layout.add_widget(self.feedback_label)

        self.scroll = ScrollView()
        self.barcode_list = GridLayout(cols=1, size_hint_y=None, spacing=5)
        self.barcode_list.bind(minimum_height=self.barcode_list.setter('height'))
        self.scroll.add_widget(self.barcode_list)
        layout.add_widget(self.scroll)

        layout.add_widget(create_bottom_nav(self))
        self.add_widget(layout)

        # Fill barcode list
        self.barcode_list.clear_widgets()
        for code in self.manager.generated_barcodes:
            self.barcode_list.add_widget(Label(text=code, size_hint_y=None, height=30))

    def check_barcode(self, instance):
        code = self.scan_input.text.strip()
        if code in self.manager.generated_barcodes:
            if code in self.manager.scanned_barcodes:
                self.feedback_label.text = "Already scanned"
            else:
                self.manager.scanned_barcodes.add(code)
                self.feedback_label.text = "Valid and scanned"
        else:
            self.feedback_label.text = "Invalid barcode"


class StatsScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        total = len(self.manager.generated_barcodes)
        scanned = len(self.manager.scanned_barcodes)
        remaining = total - scanned
        layout.add_widget(Label(text=f"Total: {total}\nScanned: {scanned}\nRemaining: {remaining}"))
        layout.add_widget(create_bottom_nav(self))
        self.add_widget(layout)


class BarcodeApp(App):
    def build(self):
        sm = ScreenManager()
        sm.generated_barcodes = []
        sm.scanned_barcodes = set()
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(StartSessionScreen(name='start'))
        sm.add_widget(LoadSessionScreen(name='load'))
        sm.add_widget(StatsScreen(name='stats'))
        return sm


if __name__ == '__main__':
    BarcodeApp().run()
