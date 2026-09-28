from PySide6.QtCore import QSize


def card_height_for_width(card, width: int, maximum_height: int) -> int:
    """Return the compact layout height for the card's actual display width."""
    layout = card.layout()
    if layout is None:
        return min(card.sizeHint().height(), maximum_height)

    height = layout.heightForWidth(width) if layout.hasHeightForWidth() else -1
    if height < 0:
        height = layout.sizeHint().height()

    minimum_height = max(card.minimumHeight(), layout.minimumSize().height())
    # A wrapped label or full-size pixmap can report a minimum larger than the
    # card's explicit cap. The cap must win or the invisible list row remains
    # much taller than the visible card.
    return min(maximum_height, max(minimum_height, height))


def compact_card_size_hint(card, hint: QSize, maximum_height: int) -> QSize:
    """Correct the early size hint Qt calculates before a list assigns width."""
    width = card.width() if card.width() > 0 else hint.width()
    hint.setHeight(card_height_for_width(card, width, maximum_height))
    return hint


def fit_list_cards(list_widget) -> None:
    """Keep card widths symmetric and row heights responsive to text wrapping."""
    for row in range(list_widget.count()):
        item = list_widget.item(row)
        card = list_widget.itemWidget(item)
        if card is None:
            continue

        item_rect = list_widget.visualItemRect(item)
        if not item_rect.isValid() or item_rect.width() <= 0:
            continue

        # QListWidget applies the item margin before positioning the card. Reuse
        # the measured left inset on the right so both sides remain identical.
        left_inset = max(0, card.x() - item_rect.x())
        top_inset = max(0, card.y() - item_rect.y())
        card_width = item_rect.width() - (left_inset * 2)
        if card_width <= 0:
            continue

        card.setFixedWidth(card_width)
        card.layout().activate()
        item_size = item.sizeHint()
        item_size.setWidth(0)
        item_size.setHeight(
            card_height_for_width(card, card_width, card.MAX_CARD_HEIGHT)
            + (top_inset * 2)
        )
        if item_size != item.sizeHint():
            item.setSizeHint(item_size)
