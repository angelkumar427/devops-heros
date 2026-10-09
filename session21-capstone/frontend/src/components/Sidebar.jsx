export default function Sidebar({ lowStock }) {
  return (
    <nav className="sidebar" aria-label="Main">
      <div className="brand">
        <img src="/favicon.svg" alt="" width="32" height="32" />
        <span>StockPilot</span>
      </div>
      <ul className="nav">
        <li><a className="active" href="#products">Inventory</a></li>
        <li>
          <a href="#activity">
            Stock activity
          </a>
        </li>
        <li>
          <a href="#categories">
            Categories
          </a>
        </li>
      </ul>
      <div className="sidebar-foot">
        <span className={`dot ${lowStock ? "dot-warn" : "dot-ok"}`} />
        {lowStock ? `${lowStock} item${lowStock > 1 ? "s" : ""} need reordering` : "Stock levels healthy"}
      </div>
    </nav>
  );
}
