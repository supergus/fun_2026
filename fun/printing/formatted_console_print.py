"""Up your Python console game with formatted text!

Requirements:
    * Python 3.10+

Works great in JetBrains PyCharm console.
No idea about other consoles!

Try:    ``>>> p = FancyPrinter().demo()``

"""

__author__ = "Christopher Couch"
__license__ = "MIT"
__version__ = "0.2.0"


class FancyPrinter(object):

    def __init__(self):
        """Defines color dictionary."""

        # RGB values
        dk = 64
        med = 128
        lt = 192
        wash1 = 153  # "wash" means "to wash out a color" and make it lighter
        wash2 = 205

        # Define the colors
        self.rgb_dict = dict(

            # GREYSCALE
            black=(0, 0, 0),
            dark_grey=(dk, dk, dk),
            medium_grey=(med, med, med),
            light_grey=(lt, lt, lt),
            white=(255, 255, 255),

            # RED
            dark_red=(dk, 0, 0),
            medium_red=(med, 0, 0),
            red=(255, 0, 0),
            light_red=(255, max(wash1 - 50, 0), max(wash1 - 50, 0)),  # wash values too light; looks pink; offset 50

            # ORANGE
            dark_orange=(dk, int(dk / 2), 0),
            medium_orange=(med, int(med / 2), 0),
            orange=(255, int(255 / 2), 0),
            light_orange=(255, wash2, wash1),

            # YELLOW
            dark_yellow=(dk, dk, 0),
            medium_yellow=(med, med, 0),
            yellow=(255, 255, 0),
            light_yellow=(255, 255, wash1),

            # CHARTREUSE
            dark_chartreuse=(int(dk / 2), dk, 0),
            medium_chartreuse=(int(med / 2), med, 0),
            chartreuse=(int(255 / 2), 255, 0),
            light_chartreuse=(wash2, 255, wash1),

            # GREEN
            dark_green=(0, dk, 0),
            medium_green=(0, med, 0),
            green=(0, 255, 0),
            light_green=(wash1, 255, wash1),

            # CYAN
            dark_cyan=(0, dk, dk),
            medium_cyan=(0, med, med),
            cyan=(0, 255, 255),
            light_cyan=(wash1, 255, 255),

            # CERULEAN
            dark_cerulean=(0, int(dk / 2), dk),
            medium_cerulean=(0, int(med / 2), med),
            cerulean=(0, int(255 / 2), 255),
            light_cerulean=(wash1, wash2, 255),

            # BLUE
            dark_blue=(0, 0, dk),
            medium_blue=(0, 0, med),
            blue=(0, 0, 255),
            light_blue=(wash1, wash1, 255),

            # PURPLE
            dark_purple=(int(dk / 2), 0, dk),
            medium_purple=(int(med / 2), 0, med),
            purple=(127, 0, 255),
            light_purple=(wash2, wash1, 255),

            # MAGENTA
            dark_magenta=(dk, 0, dk),
            medium_magenta=(med, 0, med),
            magenta=(255, 0, 255),
            light_magenta=(255, wash1, 255),

            # PINK
            dark_pink=(dk, 0, int(dk / 2)),
            medium_pink=(med, 0, int(med / 2)),
            pink=(255, 0, int(255 / 2)),
            light_pink=(255, wash1, wash2),

            # SPECIAL NAMES
            normal=(med, med, med),  # "Normal" depends on console config. We'll parse this selection separately.
            hlink=(0, int(255 / 2), 255),   # cerulean
            warning=(255, 255, 0),  # yellow
            error=(255, max(wash1 - 50, 0), max(wash1 - 50, 0)),  # light_red
        )
        return

    def __repr__(self):
        return 'Console print with style!'

    def __call__(self, *args, **kwargs):
        self.fancy_print(*args, **kwargs)

    def fancy_print(self, string='Default message', **kwargs):
        """Prints text to console using a variety of formatting methods.

        Foreground colors, background colors, and format options can be arbitrarily combined.

        |
        **Foreground and background colors available:**
            * black, white, dark_grey, medium_grey, light_grey
            * red, orange, yellow, chartreuse, green, cyan, cerulean, blue, purple, magenta, pink
            * dark, medium, and light versions of the colors, e.g. 'dark_red', 'medium_green', 'light_blue'
            * Special "colors' with automatic formatting: 'hlink', 'warning', 'error', 'normal'

        |
        **Formats available:**
            * bold, dim, underscore, italic, strikethrough, framed
            * 'highlight': Black text with yellow background

        |
        For reference see: https://en.wikipedia.org/wiki/ANSI_escape_code

        Arguments:
            string (obj): Required. The text to print.
                Can also accept objects that convert nicely using str(object).

        Keyword Arguments:
            fg (str): Optional. Foreground color. If omitted, the standard terminal color will be used.
            bg (str): Optional. Background color. If omitted, the standard terminal color will be used.
            bold (Boolean): Optional. Default is False.
            underscore (Boolean): Optional. Default is False.
            italic (Boolean): Optional. Default is False.
            strikethrough (Boolean): Optional. Default is False.
            framed (Boolean): Optional. Default is False.
            highlight (Boolean): Optional. Sets background color to yellow. Default is False.
            header (Boolean): Optional. If true, string is printed between two lines of repeated '='. Default is False.
            end (str): Optional. If '', a final linebreak will not be included. Default is None.

        Returns:
            No returns.
        """

        # Convert to string if needed.
        # This means we can actually accept most objects.
        string = str(string) if not isinstance(string, str) else string

        # Parse kwargs
        f = kwargs.get('fg', 'normal')
        b = kwargs.get('bg', 'normal')
        bold = kwargs.get('bold', False)
        underscore = kwargs.get('underscore', False)
        italic = kwargs.get('italic', False)
        strikethrough = kwargs.get('strikethrough', False)
        framed = kwargs.get('framed', False)
        highlight = kwargs.get('highlight', False)
        header = kwargs.get('header', False)
        end = kwargs.get('end', None)

        # Validate kwargs
        valid_kwargs = [
            'fg',
            'bg',
            'bold',
            'underscore',
            'italic',
            'strikethrough',
            'framed',
            'highlight',
            'header',
            'end',
        ]
        for k in kwargs:
            if k not in valid_kwargs:
                msg = f'\'{k}\' is not a valid keyword argument. Valid keywords are: {valid_kwargs}'
                raise KeyError(msg)

        # Validate booleans
        for my_bool in [bold, underscore, italic, strikethrough, framed, highlight, header]:
            if not isinstance(my_bool, bool):
                msg = f'\'b\' must be Boolean but you gave type: {type(my_bool)}'
                raise TypeError(msg)

        # =========================================================
        # Initial boolean options - more follow below
        # =========================================================

        # Handle highlight option
        if highlight:
            f = 'black'
            b = 'yellow'

        # Handle header option
        if header:
            string = '\n' + '='*80 + '\n' + string + '\n' + '='*80 + '\n'

        # =========================================================
        # Special foreground "color" options
        # =========================================================


        # Handle normal option
        if f == 'normal':
            # Just use the RGB values from dict
            pass

        # Handle hlink option
        if f == 'hlink':
            f = 'cerulean'
            b = 'normal'
            underscore = True

        # Handle warning option
        if f == 'warning':
            f = 'yellow'
            b = 'normal'
            bold = True

        # Handle error option
        if f == 'error':
            f = 'light_red'
            b = 'normal'
            bold = True

        # =========================================================
        # Validate
        # =========================================================

        # Validate selections
        if f not in self.rgb_dict:
            raise RuntimeError(f'Foreground color selection \'{f}\' is invalid. '
                               f'Please choose one of:\n{list(self.rgb_dict.keys())}')
        # Validate selections
        if b not in self.rgb_dict:
            raise RuntimeError(f'Background color selection \'{b}\' is invalid. '
                               f'Please choose one of:\n{list(self.rgb_dict.keys())}')

        # =========================================================
        # Process
        # =========================================================

        # Process color selections
        f_tuple = self.rgb_dict[f]
        b_tuple = self.rgb_dict[b]
        fR, fG, fB = f_tuple[0], f_tuple[1], f_tuple[2]
        bR, bG, bB = b_tuple[0], b_tuple[1], b_tuple[2]

        # Build list of formatting attributes
        attributes = list()
        if bold:
            attributes.append('1')
        if underscore:
            attributes.append('4')
        if italic:
            attributes.append('3')
        if strikethrough:
            attributes.append('9')
        if framed:
            attributes.append('51')

        code = ';'.join(attributes)
        code = ';' + code if len(code) > 0 else code

        # Build final string for console print using 24-bit (True Color)
        if f != 'normal' and b != 'normal':
            new_str = f'\x1b[38;2;{fR};{fG};{fB}{code};48;2;{bR};{bG};{bB}m{string}\x1b[0m'
        elif f == 'normal' and b != 'normal':
            new_str = f'\x1b[{code};48;2;{bR};{bG};{bB}m{string}\x1b[0m'
        elif f != 'normal' and b == 'normal':
            new_str = f'\x1b[38;2;{fR};{fG};{fB}{code}m{string}\x1b[0m'
        else:
            new_str = f'\x1b[{code}m{string}\x1b[0m'

        # Print to console
        print(new_str, end=end)

        return

    def demo(self, string='Foo Fighters Rule'):
        """Prints a demo to console."""

        special_fg_colors = ['normal', 'hlink', 'warning', 'error']

        self.fancy_print('FOREGROUND COLORS', fg='light_cerulean', header=True)

        # Show all colors - foreground
        for c in self.rgb_dict:
            if c not in special_fg_colors:
                print(f'\t> {c}: '.ljust(25, ' '), end='')
                self.fancy_print(string, fg=c, bold=True)

        self.fancy_print('BACKGROUND COLORS', fg='light_cerulean', header=True)

        # Show all colors - background
        for c in self.rgb_dict:
            if c not in special_fg_colors:
                print(f'\t> {c}:'.ljust(25, ' '), end='')
                self.fancy_print(string, fg='light_grey', bg=c, bold=False)

        # Show special "colors" with additional treatments
        self.fancy_print('SPECIAL FOREGROUND COLORS WITH AUTOMATIC TREATMENTS', fg='light_cerulean', header=True)
        for c in special_fg_colors:
            print(f'\t> {c}:'.ljust(25, ' '), end='')
            self.fancy_print(string, fg=c)

        self.fancy_print('FORMATTING WITH BOOLEAN FLAGS', fg='light_cerulean', header=True)

        # Some formatting
        options = ['bold', 'italic', 'underscore', 'strikethrough', 'framed', 'highlight']
        for o in options:
            kwarg_dict = {'fg': 'light_cerulean', o: True}
            print(f'\t> {o}:'.ljust(25, ' '), end='')
            self.fancy_print(string, **kwarg_dict)

        return


def fancy_print(string=None, **kwargs):
    """Prints text to console using a variety of formatting methods.

    Foreground colors, background colors, and format options can be arbitrarily combined.

    |
    **Foreground and background colors available:**
        * black, white, dark_grey, medium_grey, light_grey
        * red, orange, yellow, chartreuse, green, cyan, cerulean, blue, purple, magenta, pink
        * dark, medium, and light versions of the colors, e.g. 'dark_red', 'medium_green', 'light_blue'
        * Special "colors' with automatic formatting: 'hlink', 'warning', 'error', 'normal'

    |
    **Formats available:**
        * bold, dim, underscore, italic, strikethrough, framed
        * 'highlight': Black text with yellow background

    |
    For reference see: https://en.wikipedia.org/wiki/ANSI_escape_code

    Arguments:
        string (obj): Required. The text to print.
            Can also accept objects that convert nicely using str(object).

    Keyword Arguments:
        fg (str): Optional. Foreground color. If omitted, the standard terminal color will be used.
        bg (str): Optional. Background color. If omitted, the standard terminal color will be used.
        bold (Boolean): Optional. Default is False.
        underscore (Boolean): Optional. Default is False.
        italic (Boolean): Optional. Default is False.
        strikethrough (Boolean): Optional. Default is False.
        framed (Boolean): Optional. Default is False.
        highlight (Boolean): Optional. Sets background color to yellow. Default is False.
        header (Boolean): Optional. If true, string is printed between two lines of repeated '='. Default is False.
        end (str): Optional. If '', a final linebreak will not be included. Default is None.
        demo (bool): Optional. If True, a demonstration will be printed to the console.

    Returns:
        No returns.
    """
    demo = kwargs.get('demo', False)
    p = FancyPrinter()

    if demo:
        p.demo(string)
    else:
        p.fancy_print(string, **kwargs)
    return


